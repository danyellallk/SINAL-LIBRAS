#!/usr/bin/env python3
"""Treina um protótipo causal CTC para sequências contínuas de Libras -> palavras em português.

Entrada JSONL: cada linha deve conter:
  frames: lista temporal de vetores numéricos (318 landmarks UECE ou 360 features do app)
  portuguese_text: frase-alvo em português
  split: train/dev/test
  signer_id: pseudônimo do participante
Este modelo é experimental; não equivale a um tradutor validado.
"""
import argparse
import json
import math
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset


def tokenize(text):
    text = unicodedata.normalize("NFC", str(text or "").lower())
    return re.findall(r"[\wÀ-ÿ]+|[^\w\s]", text, flags=re.UNICODE)


def read_rows(path):
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"JSON inválido na linha {line_no}: {exc}")
        frames = row.get("frames")
        text = str(row.get("portuguese_text", "")).strip()
        split = row.get("split")
        signer = str(row.get("signer_id", "")).strip()
        if not isinstance(frames, list) or len(frames) < 2 or not text or split not in {"train", "dev", "test"} or not signer:
            raise SystemExit(f"Linha {line_no}: exige frames (>=2), portuguese_text, split train/dev/test e signer_id.")
        rows.append(row)
    if not rows:
        raise SystemExit("O JSONL não contém amostras.")
    return rows


def minimum_ctc_frames(tokens):
    # CTC precisa de um quadro extra entre tokens adjacentes repetidos.
    return len(tokens) + sum(1 for a, b in zip(tokens, tokens[1:]) if a == b)


def get_features(row, feature_dim):
    result = []
    for frame_index, frame in enumerate(row["frames"]):
        if not isinstance(frame, list) or len(frame) != feature_dim:
            raise ValueError(f"Amostra {row.get('sample_id', '?')}: quadro {frame_index} deve ter {feature_dim} valores.")
        values = [float(x) for x in frame]
        if not all(math.isfinite(x) for x in values):
            raise ValueError("Foram encontrados valores NaN ou infinitos nos landmarks.")
        result.append(values)
    return result


class ContinuousDataset(Dataset):
    def __init__(self, rows, vocab, feature_dim):
        self.rows, self.vocab, self.feature_dim = rows, vocab, feature_dim

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        frames = torch.tensor(get_features(row, self.feature_dim), dtype=torch.float32)
        tokens = tokenize(row["portuguese_text"])
        target = torch.tensor([self.vocab[t] for t in tokens if t in self.vocab], dtype=torch.long)
        return frames, target, row.get("sample_id", str(index))


def collate(batch):
    frames, targets, ids = zip(*batch)
    lengths = torch.tensor([len(x) for x in frames], dtype=torch.long)
    x = pad_sequence(frames, batch_first=True)
    y_lengths = torch.tensor([len(y) for y in targets], dtype=torch.long)
    y = torch.cat(targets) if sum(y_lengths).item() else torch.empty(0, dtype=torch.long)
    return x, lengths, y, y_lengths, ids


class CausalSignTranslator(nn.Module):
    """Encoder GRU unidirecional: não olha quadros futuros; apropriado para testes de streaming."""
    def __init__(self, feature_dim, vocab_size, hidden=192):
        super().__init__()
        self.input_norm = nn.LayerNorm(feature_dim)
        self.input_projection = nn.Sequential(
            nn.Linear(feature_dim, hidden),
            nn.GELU(),
            nn.Dropout(0.15),
        )
        self.temporal = nn.GRU(hidden, hidden, batch_first=True, bidirectional=False)
        self.classifier = nn.Sequential(nn.Dropout(0.15), nn.Linear(hidden, vocab_size))

    def forward(self, x, hidden=None, return_hidden=False):
        x = self.input_projection(self.input_norm(x))
        x, hidden = self.temporal(x, hidden)
        logits = self.classifier(x)
        return (logits, hidden) if return_hidden else logits


def greedy_decode(log_probs, lengths, id_to_token, blank=0):
    decoded = []
    for batch_index, length in enumerate(lengths.tolist()):
        ids = log_probs[:length, batch_index].argmax(dim=-1).tolist()
        tokens, previous = [], None
        for token_id in ids:
            if token_id != blank and token_id != previous:
                tokens.append(id_to_token[token_id])
            previous = token_id
        decoded.append(tokens)
    return decoded


def evaluate(model, loader, criterion, device, id_to_token):
    model.eval()
    total_loss = 0.0
    count = 0
    predictions = []
    with torch.no_grad():
        for x, lengths, targets, target_lengths, ids in loader:
            x, lengths = x.to(device), lengths.to(device)
            targets, target_lengths = targets.to(device), target_lengths.to(device)
            logits = model(x)
            log_probs = logits.log_softmax(-1).transpose(0, 1)
            loss = criterion(log_probs, targets, lengths, target_lengths)
            total_loss += float(loss.item()) * len(ids)
            count += len(ids)
            predictions.extend(zip(ids, greedy_decode(log_probs.cpu(), lengths.cpu(), id_to_token)))
    return (total_loss / max(count, 1)), predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="JSONL normalizado com frames e portuguese_text")
    parser.add_argument("--output", type=Path, default=Path("training/continuous_model"))
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--hidden", type=int, default=192)
    parser.add_argument("--min-token-count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.hidden < 8 or args.min_token_count < 1:
        raise SystemExit("Parâmetros inválidos.")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    rows = read_rows(args.dataset)
    train_rows = [r for r in rows if r["split"] == "train"]
    dev_rows = [r for r in rows if r["split"] == "dev"]
    test_rows = [r for r in rows if r["split"] == "test"]
    if not train_rows or not dev_rows:
        raise SystemExit("São necessárias amostras nos grupos train e dev. Preserve a divisão oficial por participante.")
    signer_splits = {}
    for row in rows:
        signer = str(row["signer_id"])
        signer_splits.setdefault(signer, set()).add(row["split"])
    leaking = [s for s, splits in signer_splits.items() if len(splits) > 1]
    if leaking:
        raise SystemExit(f"Vazamento: {len(leaking)} pseudônimos aparecem em mais de uma partição. Corrija os splits por participante.")

    first_frame = train_rows[0]["frames"][0]
    feature_dim = len(first_frame)
    if feature_dim < 3:
        raise SystemExit("Vetor de landmarks muito pequeno.")
    token_counts = Counter(token for row in train_rows for token in tokenize(row["portuguese_text"]))
    tokens = sorted(t for t, n in token_counts.items() if n >= args.min_token_count)
    if not tokens:
        raise SystemExit("Nenhuma palavra-alvo permaneceu após o filtro de frequência.")
    vocab = {token: i + 1 for i, token in enumerate(tokens)}  # 0 = CTC blank
    id_to_token = {i: t for t, i in vocab.items()}
    unknown_dev = sum(t not in vocab for row in dev_rows for t in tokenize(row["portuguese_text"]))
    if unknown_dev:
        print(f"AVISO: {unknown_dev} tokens de validação não existem no vocabulário de treino.")

    # Remove frases sem tokens representáveis ou curtas demais para o alinhamento CTC.
    def usable(row):
        target = [t for t in tokenize(row["portuguese_text"]) if t in vocab]
        return bool(target) and len(row["frames"]) >= minimum_ctc_frames(target)

    before = (len(train_rows), len(dev_rows), len(test_rows))
    train_rows = [r for r in train_rows if usable(r)]
    dev_rows = [r for r in dev_rows if usable(r)]
    test_rows = [r for r in test_rows if usable(r)]
    print("Amostras descartadas por alvo vazio/curto para CTC:",
          {"train": before[0] - len(train_rows), "dev": before[1] - len(dev_rows), "test": before[2] - len(test_rows)})
    if not train_rows or not dev_rows:
        raise SystemExit("Após validação CTC, faltam amostras em train ou dev. Revise comprimento das sequências e anotações.")

    train_ds = ContinuousDataset(train_rows, vocab, feature_dim)
    dev_ds = ContinuousDataset(dev_rows, vocab, feature_dim)
    test_ds = ContinuousDataset([r for r in test_rows if any(t in vocab for t in tokenize(r["portuguese_text"]))], vocab, feature_dim)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, collate_fn=collate)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, collate_fn=collate) if len(test_ds) else None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CausalSignTranslator(feature_dim, len(vocab) + 1, args.hidden).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0005, weight_decay=0.0001)
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    best_dev = float("inf")
    best_state = None

    for epoch in range(1, args.epochs + 1):
        model.train()
        running, batches = 0.0, 0
        for x, lengths, targets, target_lengths, _ in train_loader:
            x, lengths = x.to(device), lengths.to(device)
            targets, target_lengths = targets.to(device), target_lengths.to(device)
            optimizer.zero_grad()
            logits = model(x)
            log_probs = logits.log_softmax(-1).transpose(0, 1)
            loss = criterion(log_probs, targets, lengths, target_lengths)
            if not torch.isfinite(loss):
                continue
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            running += float(loss.item())
            batches += 1
        dev_loss, _ = evaluate(model, dev_loader, criterion, device, id_to_token)
        print(f"Época {epoch:03d}/{args.epochs} | perda treino {running / max(batches,1):.4f} | perda dev {dev_loss:.4f}")
        if math.isfinite(dev_loss) and dev_loss < best_dev:
            best_dev = dev_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is None:
        raise SystemExit("Não foi possível selecionar um checkpoint válido.")
    model.load_state_dict(best_state)
    test_loss = None
    if test_loader:
        test_loss, _ = evaluate(model, test_loader, criterion, device, id_to_token)

    args.output.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "feature_dim": feature_dim,
        "hidden": args.hidden,
        "vocab": vocab,
        "architecture": "causal-gru-ctc-v1",
    }, args.output / "sinal_libras_continuous_ctc.pt")
    metadata = {
        "architecture": "causal-gru-ctc-v1",
        "feature_dim": feature_dim,
        "vocabulary_size": len(vocab),
        "train_samples": len(train_ds),
        "dev_samples": len(dev_ds),
        "test_samples": len(test_ds),
        "best_dev_ctc_loss": best_dev,
        "test_ctc_loss": test_loss,
        "device": str(device),
        "signer_leakage_check": "passed",
        "warning": "Protótipo experimental. CTC produz palavras aproximadas, não garante tradução gramatical em Libras. Não usar para decisões críticas.",
    }
    (args.output / "metrics.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "vocab.json").write_text(json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
