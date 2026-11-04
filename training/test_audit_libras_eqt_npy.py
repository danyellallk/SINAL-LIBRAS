#!/usr/bin/env python3
"""Teste de regressão: auditoria mantém dimensões 126 e 318 separadas."""
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np


def main():
    script = Path(__file__).with_name("audit_libras_eqt_npy.py")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        archive = root / "fixture.zip"
        report = root / "report.json"
        with zipfile.ZipFile(archive, "w") as zf:
            for group, label, dim in (
                ("Hand Landmarks", "SINAL_A", 126),
                ("Full Landmarks", "FRASE_B", 318),
            ):
                buffer = __import__("io").BytesIO()
                np.save(buffer, np.full((4, dim), 0.25, dtype=np.float32), allow_pickle=False)
                zf.writestr(f"Landmarks/{group}/{label}/INFORMANTE 1/sample.npy", buffer.getvalue())

        run = subprocess.run(
            [sys.executable, str(script), str(archive), "--compact", "--output-json", str(report)],
            check=True, capture_output=True, text=True,
        )
        compact = json.loads(run.stdout)
        full = json.loads(report.read_text(encoding="utf-8"))

        assert full["feature_dimension_file_counts"] == {"126": 1, "318": 1}
        assert set(full["coordinate_statistics_by_feature_dimension"]) == {"126", "318"}
        assert len(full["coordinate_statistics_by_feature_dimension"]["126"]) == 126
        assert len(full["coordinate_statistics_by_feature_dimension"]["318"]) == 318
        summaries = compact["coordinate_summaries_by_feature_dimension"]
        assert summaries["126"]["coordinate_count"] == 126
        assert summaries["318"]["coordinate_count"] == 318
        assert summaries["126"]["coordinate_mean_range"] == [0.25, 0.25]
        assert summaries["318"]["coordinate_mean_range"] == [0.25, 0.25]
        assert "coordinate_mean_range" not in compact, "Não pode misturar dimensões no resumo global"
        assert full["errors_count"] == 0
    print("OK: dimensões 126 e 318 auditadas separadamente; resumo compacto consistente.")


if __name__ == "__main__":
    main()
