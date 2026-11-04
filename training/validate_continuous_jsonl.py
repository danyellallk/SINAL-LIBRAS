#!/usr/bin/env python3
"""Audita JSONL normalizado antes de treinar o SINAL LIBRAS."""
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--expected-dim", type=int, choices=(318, 360), default=None,
                        help="318 = 106 landmarks x/y/z; 360 = vetor atual do app.")
    args = parser.parse_args()

    counts = Counter()
    dimensions = Counter()
    global_dimensions = set()
    signers = defaultdict(set)
    sample_ids = set()
    issues = []
    total_frames = 0

    with args.dataset.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            counts["rows"] += 1
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                issues.append(f"Linha {line_no}: JSON inválido ({exc})")
                continue

            sample_id = str(row.get("sample_id", "")).strip()
            signer_id = str(row.get("signer_id", "")).strip()
            split = row.get("split")
            text = str(row.get("portuguese_text", "")).strip()
            frames = row.get("frames")

            if not sample_id:
                issues.append(f"Linha {line_no}: sample_id ausente")
            elif sample_id in sample_ids:
                issues.append(f"Linha {line_no}: sample_id duplicado: {sample_id}")
            sample_ids.add(sample_id)

            if not signer_id:
                issues.append(f"Linha {line_no}: signer_id ausente")
            if split not in ("train", "dev", "test"):
                issues.append(f"Linha {line_no}: split inválido: {split!r}")
            else:
                counts[f"split_{split}"] += 1
                if signer_id:
                    signers[signer_id].add(split)
            if not text:
                issues.append(f"Linha {line_no}: tradução portuguesa vazia")
            if not isinstance(frames, list) or len(frames) < 2:
                issues.append(f"Linha {line_no}: frames precisa ter ao menos 2 quadros")
                continue

            total_frames += len(frames)
            counts["frames"] += len(frames)
            frame_dim = None
            for frame_no, frame in enumerate(frames):
                if not isinstance(frame, list):
                    issues.append(f"Linha {line_no}, quadro {frame_no}: não é uma lista")
                    continue
                frame_dim = len(frame) if frame_dim is None else frame_dim
                if len(frame) != frame_dim:
                    issues.append(f"Linha {line_no}, quadro {frame_no}: dimensão inconsistente")
                    continue
                dimensions[len(frame)] += 1
                global_dimensions.add(len(frame))
                if len(frame) not in (318, 360):
                    issues.append(f"Linha {line_no}, quadro {frame_no}: dimensão {len(frame)} não reconhecida; use 318 (UECE) ou 360 (app)")
                if args.expected_dim and len(frame) != args.expected_dim:
                    issues.append(f"Linha {line_no}, quadro {frame_no}: dimensão {len(frame)}, esperado {args.expected_dim}")
                for value in frame:
                    try:
                        if not math.isfinite(float(value)):
                            raise ValueError()
                    except (TypeError, ValueError):
                        issues.append(f"Linha {line_no}, quadro {frame_no}: valor não numérico/finito")
                        break

    if len(global_dimensions) > 1:
        issues.append(f"Dimensões diferentes entre quadros/amostras: {sorted(global_dimensions)}")

    leakage = {s: sorted(parts) for s, parts in signers.items() if len(parts) > 1}
    if leakage:
        issues.append(f"Vazamento de participantes entre splits: {len(leakage)} IDs. Exemplos: {list(leakage.items())[:5]}")

    print("Resumo:", json.dumps({
        "amostras": counts["rows"],
        "quadros": total_frames,
        "por_particao": {s: counts[f"split_{s}"] for s in ("train", "dev", "test")},
        "dimensoes_dos_vetores": dict(dimensions),
        "participantes": len(signers),
        "ids_com_vazamento": len(leakage),
    }, ensure_ascii=False, indent=2))
    if issues:
        print(f"FALHAS: {len(issues)}")
        for issue in issues[:100]:
            print("-", issue)
        if len(issues) > 100:
            print(f"... e mais {len(issues) - 100} falhas")
        raise SystemExit(1)
    print("OK: estrutura básica consistente. Isso não valida a correção linguística das traduções.")


if __name__ == "__main__":
    main()
