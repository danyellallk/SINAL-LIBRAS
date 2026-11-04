#!/usr/bin/env python3
"""Validate and normalize SINAL LIBRAS v2 sample exports using only Python stdlib."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

FACE_IDS = {1, 13, 14, 33, 61, 105, 133, 159, 234, 263, 291, 334, 362, 386, 454}
HAND_POINTS = 21
BODY_POINTS = 33
FACE_POINTS = 15
FRAME_COUNT = 12


def point_map(points, expected):
    result = [[0.0, 0.0, 0.0, 0.0] for _ in range(expected)]
    for item in points or []:
        idx = item.get("point")
        if isinstance(idx, int) and 0 <= idx < expected:
            result[idx] = [
                float(item.get("x", 0.0)),
                float(item.get("y", 0.0)),
                float(item.get("z", 0.0)),
                float(item.get("visibility", 1.0)),
            ]
    return result


def canonical_frame(frame):
    hands = frame.get("hands") or []
    left = [[0.0, 0.0, 0.0, 0.0] for _ in range(HAND_POINTS)]
    right = [[0.0, 0.0, 0.0, 0.0] for _ in range(HAND_POINTS)]
    for hand in hands[:2]:
        target = left if str(hand.get("handedness", "")).lower() == "left" else right
        target[:] = point_map(hand.get("points"), HAND_POINTS)
    face = []
    source_face = frame.get("face") or []
    by_id = {p.get("point"): p for p in source_face}
    for point_id in sorted(FACE_IDS):
        p = by_id.get(point_id)
        face.append([
            float(p.get("x", 0.0)) if p else 0.0,
            float(p.get("y", 0.0)) if p else 0.0,
            float(p.get("z", 0.0)) if p else 0.0,
            1.0 if p else 0.0,
        ])
    return {
        "time_seconds": float(frame.get("timeSeconds", 0.0)),
        "hands": {"left": left, "right": right},
        "body": point_map(frame.get("body"), BODY_POINTS),
        "face": face,
    }


def split_for_signer(signer_id):
    value = str(signer_id or "sem-identificador")
    h = 0
    encoded = value.encode("utf-16-le")
    for index in range(0, len(encoded), 2):
        code_unit = encoded[index] | (encoded[index + 1] << 8)
        h = (h * 31 + code_unit) & 0xFFFFFFFF
    bucket = h % 20
    return "teste" if bucket < 3 else ("validacao" if bucket < 6 else "treino")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON exportado pelo SINAL LIBRAS")
    parser.add_argument("--output", type=Path, default=Path("prepared_dataset.jsonl"))
    parser.add_argument("--include-drafts", action="store_true", help="Inclui exemplos ainda não declarados como revisados")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    samples = payload.get("samples")
    if not isinstance(samples, list):
        raise SystemExit("Arquivo inválido: não encontrei a lista 'samples'.")

    prepared = []
    skipped = Counter()
    labels_by_split = defaultdict(Counter)
    signer_by_label = defaultdict(set)

    for sample in samples:
        label = str(sample.get("label", "")).strip()
        signer = str(sample.get("signerId", "")).strip()
        frames = sample.get("frames")
        if not label or not signer:
            skipped["sem_rotulo_ou_pseudonimo"] += 1
            continue
        if not args.include_drafts and sample.get("reviewStatus") != "revisado":
            skipped["rascunho_ou_sem_revisao_declarada"] += 1
            continue
        if not sample.get("permissionConfirmed"):
            skipped["sem_confirmacao_de_autorizacao"] += 1
            continue
        if not isinstance(frames, list) or not frames:
            skipped["sem_sequencia"] += 1
            continue

        frames = sorted(frames, key=lambda f: float(f.get("timeSeconds", 0.0)))
        canonical = [canonical_frame(f) for f in frames]
        split = split_for_signer(signer)
        record = {
            "schema": "sinal-libras-sequence-v1",
            "label": label,
            "meaning_or_context": str(sample.get("meaningOrContext", "")),
            "signer_id": signer,
            "split": split,
            "review_status": sample.get("reviewStatus", "rascunho"),
            "review_is_self_declared": True,
            "permission_confirmed_by_uploader": True,
            "source_sample_id": sample.get("id"),
            "frames": canonical,
        }
        prepared.append(record)
        labels_by_split[split][label] += 1
        signer_by_label[label].add(signer)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for item in prepared:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")

    summary = {
        "input_samples": len(samples),
        "prepared_samples": len(prepared),
        "skipped": dict(skipped),
        "split_counts": dict(Counter(item["split"] for item in prepared)),
        "labels_by_split": {k: dict(v) for k, v in labels_by_split.items()},
        "distinct_signers_per_label": {k: len(v) for k, v in signer_by_label.items()},
        "warnings": [
            "Este script prepara dados; não treina um modelo nem reconhece Libras.",
            "A revisão e a autorização são declarações do responsável pelo envio e não são verificadas automaticamente.",
            "A divisão por pseudônimo pode deixar classes ou grupos sem exemplos; confira o resumo antes de treinar.",
            "Uma amostra de sinal isolado não ensina, por si só, gramática ou tradução de frases completas.",
        ],
    }
    summary_path = args.output.with_name("dataset_summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nDados preparados: {args.output}")
    print(f"Resumo: {summary_path}")


if __name__ == "__main__":
    main()
