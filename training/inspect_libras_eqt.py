#!/usr/bin/env python3
"""Inspeciona um ZIP de landmarks sem extrair o arquivo nem executar dados serializados."""
import argparse
import ast
import csv
import io
import json
import struct
import zipfile
from collections import Counter
from pathlib import Path

MAX_TEXT_SAMPLE = 1024 * 1024
MAX_ARCHIVE_ENTRIES = 200000


def npy_header(data):
    if len(data) < 10 or data[:6] != b"\x93NUMPY":
        return {"error": "cabecalho NPY invalido"}
    major, minor = data[6], data[7]
    if major == 1:
        header_len = struct.unpack("<H", data[8:10])[0]
        offset = 10
    elif major in (2, 3):
        if len(data) < 12:
            return {"error": "cabecalho NPY incompleto"}
        header_len = struct.unpack("<I", data[8:12])[0]
        offset = 12
    else:
        return {"version": f"{major}.{minor}", "error": "versao NPY desconhecida"}
    if header_len > 65536 or len(data) < offset + header_len:
        return {"error": "cabecalho NPY muito grande ou incompleto"}
    raw = data[offset:offset + header_len]
    try:
        header = ast.literal_eval(raw.decode("latin1").strip())
    except (ValueError, SyntaxError):
        return {"error": "nao foi possivel interpretar o cabecalho"}
    return {
        "version": f"{major}.{minor}",
        "shape": header.get("shape"),
        "fortran_order": header.get("fortran_order"),
        "dtype": str(header.get("descr")),
        "requires_pickle_to_load": "O" in str(header.get("descr")),
    }


def inspect_text_member(archive, info):
    if info.file_size > MAX_TEXT_SAMPLE:
        return {"inspection": "ignorado: amostra maior que 1 MB", "uncompressed_bytes": info.file_size}
    raw = archive.read(info)
    suffix = Path(info.filename).suffix.lower()
    if suffix == ".json":
        try:
            obj = json.loads(raw.decode("utf-8-sig"))
            if isinstance(obj, dict):
                return {"json_top_level": "object", "keys": list(obj)[:40]}
            if isinstance(obj, list):
                return {"json_top_level": "array", "items_in_sample": len(obj), "first_item_type": type(obj[0]).__name__ if obj else None}
            return {"json_top_level": type(obj).__name__}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return {"inspection_error": str(exc)}
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                text = raw.decode(encoding)
                rows = list(csv.reader(io.StringIO(text)))
                return {"csv_encoding": encoding, "columns": rows[0][:50] if rows else [], "sample_rows": max(0, min(3, len(rows)-1))}
            except UnicodeDecodeError:
                continue
        return {"inspection_error": "encoding CSV nao reconhecido"}
    return {}


def inspect_archive(path, limit):
    if not path.is_file():
        raise SystemExit(f"Arquivo nao encontrado: {path}")
    with zipfile.ZipFile(path) as archive:
        infos = [i for i in archive.infolist() if not i.is_dir()]
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise SystemExit(f"Arquivo contem mais de {MAX_ARCHIVE_ENTRIES} itens; inspeção interrompida por segurança.")
        extensions = Counter(Path(i.filename).suffix.lower() or "[sem extensao]" for i in infos)
        total_uncompressed = sum(i.file_size for i in infos)
        print(json.dumps({
            "archive": str(path),
            "files": len(infos),
            "compressed_bytes": path.stat().st_size,
            "uncompressed_bytes": total_uncompressed,
            "extensions": dict(extensions),
            "note": "Inspecao somente de metadados e pequenas amostras; nenhum arquivo foi extraido.",
        }, ensure_ascii=False, indent=2))
        inspected = 0
        for info in infos:
            suffix = Path(info.filename).suffix.lower()
            if suffix not in {".csv", ".json", ".npy"}:
                continue
            if inspected >= limit:
                break
            result = {"file": info.filename, "uncompressed_bytes": info.file_size}
            if suffix == ".npy":
                with archive.open(info) as member:
                    result.update(npy_header(member.read(65548)))
            else:
                result.update(inspect_text_member(archive, info))
            print(json.dumps(result, ensure_ascii=False))
            inspected += 1
        if inspected == 0:
            print("Nenhum CSV, JSON ou NPY encontrado na amostra de arquivos.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Caminho para Landmarks.zip ou outro ZIP de dados")
    parser.add_argument("--limit", type=int, default=25, help="Quantidade máxima de arquivos de dados a inspecionar")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 500:
        raise SystemExit("--limit deve ficar entre 1 e 500.")
    try:
        inspect_archive(args.archive, args.limit)
    except zipfile.BadZipFile:
        raise SystemExit("O arquivo nao e um ZIP valido ou esta corrompido.")
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Falha ao inspecionar o ZIP: {exc}")


if __name__ == "__main__":
    main()
