#!/usr/bin/env python3
"""Inspeciona a estrutura do pacote contínuo UECE sem extrair nem desserializar arrays."""
import argparse
import ast
import json
import struct
import zipfile
from collections import Counter
from pathlib import Path

MAX_ENTRIES = 500_000
MAX_HEADER = 65_536


def read_npy_header(stream):
    prefix = stream.read(8)
    if len(prefix) != 8 or prefix[:6] != b"\x93NUMPY":
        return {"header_error": "not_npy_or_truncated"}
    major, minor = prefix[6], prefix[7]
    if major == 1:
        length_bytes = stream.read(2)
        if len(length_bytes) != 2:
            return {"header_error": "truncated_npy_header"}
        header_len = struct.unpack("<H", length_bytes)[0]
    elif major in (2, 3):
        length_bytes = stream.read(4)
        if len(length_bytes) != 4:
            return {"header_error": "truncated_npy_header"}
        header_len = struct.unpack("<I", length_bytes)[0]
    else:
        return {"header_error": "unsupported_npy_version", "version": f"{major}.{minor}"}
    if header_len > MAX_HEADER:
        return {"header_error": "header_too_large", "header_bytes": header_len}
    raw = stream.read(header_len)
    if len(raw) != header_len:
        return {"header_error": "truncated_npy_header"}
    try:
        header = ast.literal_eval(raw.decode("latin1").strip())
    except (ValueError, SyntaxError):
        return {"header_error": "invalid_npy_header"}
    descr = header.get("descr")
    return {
        "npy_version": f"{major}.{minor}",
        "shape": header.get("shape"),
        "dtype": str(descr),
        "fortran_order": header.get("fortran_order"),
        "object_or_pickle_dtype": "O" in str(descr),
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Caminho para Libras-EQT-UECE-T.zip")
    parser.add_argument("--samples", type=int, default=30, help="Máximo de cabeçalhos NPY para inspecionar")
    args = parser.parse_args()
    if not 1 <= args.samples <= 500:
        raise SystemExit("--samples deve ficar entre 1 e 500.")
    if not args.archive.is_file():
        raise SystemExit(f"Arquivo não encontrado: {args.archive}")

    try:
        with zipfile.ZipFile(args.archive) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            if len(infos) > MAX_ENTRIES:
                raise SystemExit(f"ZIP tem mais de {MAX_ENTRIES} arquivos; inspeção interrompida.")
            ext_counts = Counter(Path(i.filename).suffix.lower() or "[sem extensão]" for i in infos)
            top_dirs = Counter(i.filename.split("/", 1)[0] for i in infos)
            annotation_candidates = [
                i for i in infos
                if any(token in i.filename.lower() for token in ("annot", "label", "gloss", "train.npy", "dev.npy", "test.npy"))
            ]
            npy_infos = [i for i in infos if Path(i.filename).suffix.lower() == ".npy"]
            print(json.dumps({
                "archive": str(args.archive),
                "files": len(infos),
                "compressed_bytes": args.archive.stat().st_size,
                "uncompressed_bytes": sum(i.file_size for i in infos),
                "extensions": dict(ext_counts),
                "top_level_directories": top_dirs.most_common(30),
                "annotation_path_candidates": [
                    {"path": i.filename, "bytes": i.file_size, "compressed_bytes": i.compress_size}
                    for i in annotation_candidates[:200]
                ],
                "npy_file_count": len(npy_infos),
                "safety": "Somente lista ZIP e lê cabeçalhos NPY. Não extrai arquivos, não carrega arrays e nunca usa pickle.",
            }, ensure_ascii=False, indent=2))

            for info in npy_infos[:args.samples]:
                result = {"path": info.filename, "bytes": info.file_size}
                try:
                    with zf.open(info) as member:
                        result.update(read_npy_header(member))
                except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                    result["inspection_error"] = str(exc)
                print(json.dumps(result, ensure_ascii=False))
    except zipfile.BadZipFile:
        raise SystemExit("O arquivo não é um ZIP válido ou está corrompido.")


if __name__ == "__main__":
    main()
