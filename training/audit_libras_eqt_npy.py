#!/usr/bin/env python3
"""Auditoria detalhada de NPY de landmarks dentro de ZIP, sem extrair arquivos."""
import argparse
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import PurePosixPath

try:
    import numpy as np
except ImportError:
    raise SystemExit("Instale numpy antes: pip install numpy")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--limit-samples", type=int, default=8)
    parser.add_argument("--output-json", help="Salva o relatório completo neste arquivo JSON")
    parser.add_argument("--compact", action="store_true", help="Imprime um resumo curto, mantendo o JSON completo no arquivo")
    args = parser.parse_args()
    if args.limit_samples < 1 or args.limit_samples > 100:
        raise SystemExit("--limit-samples deve ficar entre 1 e 100")

    labels = Counter()
    informants = Counter()
    shapes = Counter()
    dtypes = Counter()
    errors = []
    samples = []
    frame_counts = []
    global_min = float("inf")
    global_max = float("-inf")
    finite_values = 0
    nonfinite_values = 0
    zero_values = 0
    column_min = None
    column_max = None
    column_sum = None
    column_count = None
    with zipfile.ZipFile(args.archive) as zf:
        members = [x for x in zf.infolist() if not x.is_dir() and x.filename.lower().endswith(".npy")]
        for info in members:
            parts = PurePosixPath(info.filename).parts
            # Estrutura esperada: .../(Hand Landmarks)/GLOSS/INFORMANTE N/arquivo.npy
            label = parts[-3] if len(parts) >= 3 else "[rotulo_desconhecido]"
            informant = parts[-2] if len(parts) >= 2 else "[informante_desconhecido]"
            labels[label] += 1
            informants[informant] += 1
            try:
                arr = np.load(io.BytesIO(zf.read(info)), allow_pickle=False)
                if arr.ndim != 2:
                    errors.append({"file": info.filename, "error": "array nao possui 2 dimensoes", "shape": list(arr.shape)})
                    continue
                shapes[str(list(arr.shape))] += 1
                dtypes[str(arr.dtype)] += 1
                frame_counts.append(int(arr.shape[0]))
                vals = np.asarray(arr, dtype=np.float64)
                finite = np.isfinite(vals)
                finite_count = int(finite.sum())
                finite_values += finite_count
                nonfinite_values += int(vals.size - finite_count)
                zero_values += int(np.count_nonzero(vals == 0))
                # Estatísticas por coordenada, acumuladas em todos os quadros.
                if column_min is None:
                    column_min = np.full(arr.shape[1], np.inf, dtype=np.float64)
                    column_max = np.full(arr.shape[1], -np.inf, dtype=np.float64)
                    column_sum = np.zeros(arr.shape[1], dtype=np.float64)
                    column_count = np.zeros(arr.shape[1], dtype=np.int64)
                if arr.shape[1] == len(column_min):
                    for col in range(arr.shape[1]):
                        col_values = vals[:, col]
                        col_finite = np.isfinite(col_values)
                        if col_finite.any():
                            selected = col_values[col_finite]
                            column_min[col] = min(column_min[col], float(selected.min()))
                            column_max[col] = max(column_max[col], float(selected.max()))
                            column_sum[col] += float(selected.sum())
                            column_count[col] += int(selected.size)
                if finite_count:
                    vmin = float(vals[finite].min())
                    vmax = float(vals[finite].max())
                    global_min = min(global_min, vmin)
                    global_max = max(global_max, vmax)
                if len(samples) < args.limit_samples:
                    samples.append({
                        "file": info.filename,
                        "shape": list(arr.shape),
                        "dtype": str(arr.dtype),
                        "finite_values": finite_count,
                        "nonfinite_values": int(vals.size - finite_count),
                        "first_frame_first_12_values": [float(x) for x in arr[0, :12]] if arr.shape[0] else [],
                    })
            except Exception as exc:
                errors.append({"file": info.filename, "error": f"{type(exc).__name__}: {exc}"})

    report = {
        "archive_npy_files": len(members),
        "labels_count": len(labels),
        "labels_top_100": labels.most_common(100),
        "informant_folders": dict(informants),
        "shape_distribution": dict(shapes),
        "dtype_distribution": dict(dtypes),
        "frame_count_min": min(frame_counts) if frame_counts else None,
        "frame_count_median": float(np.median(frame_counts)) if frame_counts else None,
        "frame_count_max": max(frame_counts) if frame_counts else None,
        "finite_values": finite_values,
        "nonfinite_values": nonfinite_values,
        "zero_values": zero_values,
        "zero_fraction": (zero_values / (finite_values + nonfinite_values)) if (finite_values + nonfinite_values) else None,
        "per_coordinate_statistics": [
            {
                "coordinate_index": i,
                "min": float(column_min[i]) if column_count[i] else None,
                "max": float(column_max[i]) if column_count[i] else None,
                "mean": float(column_sum[i] / column_count[i]) if column_count[i] else None,
                "finite_count": int(column_count[i]),
            }
            for i in range(len(column_min))
        ] if column_min is not None else [],
        "global_min": global_min if global_min != float("inf") else None,
        "global_max": global_max if global_max != float("-inf") else None,
        "sample_arrays": samples,
        "errors_count": len(errors),
        "errors_first_30": errors[:30],
        "warning": "A auditoria descreve estrutura e valores; nao confirma significado linguistico, particoes oficiais ou alinhamento com frases."
    }
    if args.output_json:
        from pathlib import Path
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.compact:
        coordinate_rows = report["per_coordinate_statistics"]
        valid_means = [x["mean"] for x in coordinate_rows if x["mean"] is not None]
        coordinate_mins = [x["min"] for x in coordinate_rows if x["min"] is not None]
        coordinate_maxs = [x["max"] for x in coordinate_rows if x["max"] is not None]
        compact = {
            "archive_npy_files": report["archive_npy_files"],
            "labels_count": report["labels_count"],
            "labels_top_20": report["labels_top_100"][:20],
            "informant_folders": report["informant_folders"],
            "shape_top_20": Counter(report["shape_distribution"]).most_common(20),
            "dtype_distribution": report["dtype_distribution"],
            "frame_count_min": report["frame_count_min"],
            "frame_count_median": report["frame_count_median"],
            "frame_count_max": report["frame_count_max"],
            "finite_values": report["finite_values"],
            "nonfinite_values": report["nonfinite_values"],
            "zero_fraction": report["zero_fraction"],
            "global_min": report["global_min"],
            "global_max": report["global_max"],
            "coordinate_count": len(coordinate_rows),
            "coordinates_with_data": len(valid_means),
            "coordinates_constant": sum(1 for x in coordinate_rows if x["min"] is not None and x["min"] == x["max"]),
            "coordinate_min_range": [min(coordinate_mins, default=None), max(coordinate_mins, default=None)],
            "coordinate_max_range": [min(coordinate_maxs, default=None), max(coordinate_maxs, default=None)],
            "coordinate_mean_range": [min(valid_means, default=None), max(valid_means, default=None)],
            "coordinate_first_12": coordinate_rows[:12],
            "coordinate_last_12": coordinate_rows[-12:],
            "errors_count": report["errors_count"],
            "errors_first_10": report["errors_first_30"][:10],
            "full_report_path": args.output_json,
            "warning": report["warning"],
        }
        print(json.dumps(compact, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
