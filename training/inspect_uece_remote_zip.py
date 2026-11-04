#!/usr/bin/env python3
"""Inspeciona metadados de ZIP remoto por HTTP Range, sem baixar o arquivo inteiro."""
import argparse
import ast
import json
import struct
import sys
from collections import Counter
from pathlib import PurePosixPath

MAX_HEADER = 65_536
MAX_MEMBER_PREFIX = 2 * 1024 * 1024


def npy_header(data):
    if len(data) < 10 or data[:6] != b"\x93NUMPY":
        return {"header_error": "not_npy_or_truncated"}
    major, minor = data[6], data[7]
    if major == 1:
        offset, n = 10, 2
    elif major in (2, 3):
        offset, n = 12, 4
    else:
        return {"header_error": "unsupported_version", "version": f"{major}.{minor}"}
    if len(data) < offset:
        return {"header_error": "truncated_length"}
    size = int.from_bytes(data[8:offset], "little")
    if size > MAX_HEADER or len(data) < offset + size:
        return {"header_error": "header_too_large_or_truncated", "header_bytes": size}
    try:
        h = ast.literal_eval(data[offset:offset + size].decode("latin1").strip())
    except (ValueError, SyntaxError):
        return {"header_error": "invalid_header"}
    return {
        "npy_version": f"{major}.{minor}",
        "shape": h.get("shape"),
        "dtype": str(h.get("descr")),
        "object_dtype": "O" in str(h.get("descr")),
        "header_bytes": size,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", default="21398895", help="ID do registro Zenodo")
    parser.add_argument("--file-contains", default="Libras-EQT-UECE-T.zip")
    parser.add_argument("--max-samples", type=int, default=80)
    args = parser.parse_args()
    if not 1 <= args.max_samples <= 200:
        raise SystemExit("--max-samples deve ficar entre 1 e 200")
    try:
        import requests
        from remotezip import RemoteZip
    except ImportError:
        raise SystemExit("Dependências ausentes. No Colab, execute: pip -q install remotezip requests")

    api_url = f"https://zenodo.org/api/records/{args.record}"
    response = requests.get(api_url, timeout=60)
    response.raise_for_status()
    record = response.json()
    matches = [f for f in record.get("files", []) if args.file_contains.lower() in f["key"].lower()]
    if len(matches) != 1:
        raise SystemExit("Não foi possível identificar um único ZIP contínuo: " + json.dumps([f.get("key") for f in matches]))
    item = matches[0]
    url = item.get("links", {}).get("self")
    if not url:
        raise SystemExit("A API do Zenodo não forneceu o link do arquivo.")
    print(json.dumps({
        "record": args.record,
        "file": item["key"],
        "published_size_bytes": item["size"],
        "checksum": item.get("checksum"),
        "method": "HTTP Range; somente diretório central e membros selecionados",
    }, ensure_ascii=False))

    try:
        with RemoteZip(url) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            ext = Counter(PurePosixPath(i.filename).suffix.lower() or "[sem extensão]" for i in infos)
            candidates = [i for i in infos if any(k in i.filename.lower() for k in ("annot", "label", "gloss", "train", "dev", "test"))]
            npys = [i for i in infos if i.filename.lower().endswith(".npy")]
            print(json.dumps({
                "member_count": len(infos),
                "extensions": dict(ext),
                "top_annotation_candidates": [{"path": i.filename, "size": i.file_size} for i in candidates[:200]],
                "npy_count": len(npys),
            }, ensure_ascii=False))
            for info in npys[:args.max_samples]:
                row = {"path": info.filename, "uncompressed_bytes": info.file_size}
                try:
                    with zf.open(info) as member:
                        prefix = member.read(MAX_MEMBER_PREFIX)
                    row.update(npy_header(prefix))
                    row["prefix_bytes_read"] = len(prefix)
                    row["payload_truncated_for_safety"] = len(prefix) == MAX_MEMBER_PREFIX
                except Exception as exc:
                    row["inspection_error"] = f"{type(exc).__name__}: {exc}"
                print(json.dumps(row, ensure_ascii=False))
    except Exception as exc:
        raise SystemExit(
            f"Inspeção remota falhou ({type(exc).__name__}: {exc}). "
            "O servidor pode não aceitar HTTP Range; não foi baixado o ZIP inteiro."
        )


if __name__ == "__main__":
    main()
