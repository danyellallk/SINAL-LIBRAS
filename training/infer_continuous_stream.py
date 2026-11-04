#!/usr/bin/env python3
"""Executa o protótipo causal CTC em blocos mantendo estado entre blocos."""
import argparse
import json
from pathlib import Path

import torch
from torch import nn


class CausalSignTranslator(nn.Module):
    def __init__(self, feature_dim, vocab_size, hidden=192):
        super().__init__()
        self.input_norm = nn.LayerNorm(feature_dim)
        self.input_projection = nn.Sequential(nn.Linear(feature_dim, hidden), nn.GELU(), nn.Dropout(0.15))
        self.temporal = nn.GRU(hidden, hidden, batch_first=True, bidirectional=False)
        self.classifier = nn.Sequential(nn.Dropout(0.15), nn.Linear(hidden, vocab_size))

    def forward(self, x, hidden=None):
        x = self.input_projection(self.input_norm(x))
        x, hidden = self.temporal(x, hidden)
        return self.classifier(x), hidden


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="sinal_libras_continuous_ctc.pt")
    parser.add_argument("sequence", type=Path, help="JSON com a chave frames: lista de vetores")
    parser.add_argument("--chunk-frames", type=int, default=8, help="Quadros processados por bloco")
    args = parser.parse_args()
    if args.chunk_frames < 1:
        raise SystemExit("--chunk-frames deve ser >= 1")

    checkpoint = torch.load(args.model, map_location="cpu", weights_only=True)
    data = json.loads(args.sequence.read_text(encoding="utf-8"))
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise SystemExit("O JSON precisa conter uma lista não vazia em 'frames'.")
    feature_dim = checkpoint["feature_dim"]
    for i, frame in enumerate(frames):
        if not isinstance(frame, list) or len(frame) != feature_dim:
            raise SystemExit(f"Quadro {i}: esperado vetor com {feature_dim} valores.")

    vocab = checkpoint["vocab"]
    id_to_token = {int(i): token for token, i in vocab.items()}
    model = CausalSignTranslator(feature_dim, len(vocab) + 1, checkpoint["hidden"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    hidden = None
    previous_id = None
    emitted = []
    with torch.no_grad():
        for start in range(0, len(frames), args.chunk_frames):
            chunk = torch.tensor(frames[start:start + args.chunk_frames], dtype=torch.float32).unsqueeze(0)
            logits, hidden = model(chunk, hidden)
            ids = logits.argmax(dim=-1).squeeze(0).tolist()
            new_tokens = []
            for token_id in ids:
                if token_id != 0 and token_id != previous_id:
                    token = id_to_token.get(token_id)
                    if token:
                        emitted.append(token)
                        new_tokens.append(token)
                previous_id = token_id
            print(json.dumps({
                "processed_frames": min(start + len(ids), len(frames)),
                "total_frames": len(frames),
                "new_tokens": new_tokens,
                "provisional_text": " ".join(emitted),
            }, ensure_ascii=False))

    print("\nTexto provisório:", " ".join(emitted))
    print("A saída é experimental e precisa de revisão linguística; não é uma tradução confiável ainda.")


if __name__ == "__main__":
    main()
