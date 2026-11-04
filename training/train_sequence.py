#!/usr/bin/env python3
"""Treina um classificador experimental de sequências; não é tradutor de frases."""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

FEATURES_PER_FRAME = 360
SPLITS = {"treino", "validacao", "teste"}


def frame_vector(frame):
    values = []
    for side in ("left", "right"):
        points = frame.get("hands", {}).get(side, [])
        for point in points[:21]:
            values.extend((point + [0.0] * 4)[:4])
        for _ in range(max(0, 21 - len(points))):
            values.extend([0.0] * 4)
    for section, count in (("body", 33), ("face", 15)):
        points = frame.get(section, [])
        for point in points[:count]:
            values.extend((point + [0.0] * 4)[:4])
        for _ in range(max(0, count - len(points))):
            values.extend([0.0] * 4)
    if len(values) != FEATURES_PER_FRAME:
        raise ValueError(f"Vetor com {len(values)} valores; esperado {FEATURES_PER_FRAME}.")
    return values


class SequenceData(Dataset):
    def __init__(self, rows, label_to_id, max_frames):
        self.rows = rows
        self.label_to_id = label_to_id
        self.max_frames = max_frames

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        frames = [frame_vector(f) for f in row["frames"]]
        if len(frames) > self.max_frames:
            positions = [round(i * (len(frames) - 1) / (self.max_frames - 1)) for i in range(self.max_frames)]
            frames = [frames[i] for i in positions]
        length = len(frames)
        frames += [[0.0] * FEATURES_PER_FRAME for _ in range(self.max_frames - length)]
        return torch.tensor(frames, dtype=torch.float32), torch.tensor(length), torch.tensor(self.label_to_id[row["label"]])


class SignSequenceModel(nn.Module):
    def __init__(self, classes, hidden=96):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(FEATURES_PER_FRAME, 192),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(192, 128),
            nn.ReLU(),
        )
        self.gru = nn.GRU(128, hidden, batch_first=True, bidirectional=True)
        self.classifier = nn.Sequential(
            nn.Dropout(0.25),
            nn.Linear(hidden * 2, classes),
        )

    def forward(self, x, lengths):
        encoded = self.encoder(x)
        packed = nn.utils.rnn.pack_padded_sequence(
            encoded, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, hidden = self.gru(packed)
        final = torch.cat((hidden[-2], hidden[-1]), dim=1)
        return self.classifier(final)


def read_jsonl(path):
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"JSON inválido na linha {line_number}: {exc}")
        if row.get("split") not in SPLITS or not row.get("label") or not row.get("frames"):
            raise SystemExit(f"Registro incompleto na linha {line_number}.")
        rows.append(row)
    return rows


def evaluate(model, loader, device):
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, lengths, y in loader:
            x, lengths, y = x.to(device), lengths.to(device), y.to(device)
            prediction = model(x, lengths).argmax(dim=1)
            correct += int((prediction == y).sum().item())
            total += int(y.numel())
    return correct / total if total else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Arquivo JSONL preparado")
    parser.add_argument("--output", type=Path, default=Path("training/model"))
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-frames", type=int, default=48)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    if args.max_frames < 2 or args.epochs < 1 or args.batch_size < 1:
        raise SystemExit("--max-frames deve ser >= 2; --epochs e --batch-size devem ser >= 1.")
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    rows = read_jsonl(args.dataset)
    train_rows = [r for r in rows if r["split"] == "treino"]
    val_rows = [r for r in rows if r["split"] == "validacao"]
    test_rows = [r for r in rows if r["split"] == "teste"]
    labels = sorted({r["label"] for r in train_rows})
    if len(labels) < 2:
        raise SystemExit("São necessárias pelo menos duas classes diferentes no grupo treino.")
    label_to_id = {label: i for i, label in enumerate(labels)}
    unknown = sorted({r["label"] for r in val_rows + test_rows} - set(labels))
    if unknown:
        print("AVISO: rótulos sem exemplo no treino serão ignorados:", ", ".join(unknown))
    val_rows = [r for r in val_rows if r["label"] in label_to_id]
    test_rows = [r for r in test_rows if r["label"] in label_to_id]
    if not train_rows:
        raise SystemExit("Nenhum exemplo no grupo treino.")
    if not val_rows:
        raise SystemExit("Nenhum exemplo de validação com rótulos vistos no treino. Reúna mais sinalizadores/amostras; não use o teste para ajustar o modelo.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_data = SequenceData(train_rows, label_to_id, args.max_frames)
    val_data = SequenceData(val_rows, label_to_id, args.max_frames)
    test_data = SequenceData(test_rows, label_to_id, args.max_frames)
    train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=args.batch_size)
    test_loader = DataLoader(test_data, batch_size=args.batch_size)
    model = SignSequenceModel(len(labels)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0005)
    loss_fn = nn.CrossEntropyLoss()
    best_accuracy = -1.0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for x, lengths, y in train_loader:
            x, lengths, y = x.to(device), lengths.to(device), y.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(x, lengths), y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += float(loss.item())
        val_accuracy = evaluate(model, val_loader, device)
        if val_accuracy is not None and val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        print(f"Época {epoch:03d}/{args.epochs} | perda {total_loss / max(1, len(train_loader)):.4f} | acurácia validação {val_accuracy:.3f}")

    if best_state is None:
        raise SystemExit("Não foi possível selecionar um modelo pela validação.")
    model.load_state_dict(best_state)
    test_accuracy = evaluate(model, test_loader, device) if test_rows else None
    args.output.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "classes": labels, "features_per_frame": FEATURES_PER_FRAME, "max_frames": args.max_frames}, args.output / "sinal_libras_gru.pt")
    metadata = {
        "classes": labels,
        "train_examples": len(train_rows),
        "validation_examples": len(val_rows),
        "test_examples": len(test_rows),
        "validation_accuracy": best_accuracy,
        "test_accuracy": test_accuracy,
        "device": str(device),
        "warning": "Protótipo experimental de classificação de sinais isolados. Não traduz frases nem representa desempenho geral em Libras.",
        "train_label_counts": dict(Counter(r["label"] for r in train_rows)),
    }
    (args.output / "metrics.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "classes.json").write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
