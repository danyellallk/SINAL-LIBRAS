#!/usr/bin/env python3
"""Inspeciona opcodes pickle de NPY object sem executar nem desserializar o payload."""
import argparse
import ast
import json
import pickletools
import struct
import zipfile
from collections import Counter
from pathlib import Path

MAX_HEADER = 65_536
MAX_PAYLOAD = 64 * 1024 * 1024


def split_npy(raw):
    if len(raw) < 10 or raw[:6] != b"\x93NUMPY":
        raise ValueError("Arquivo não possui assinatura NPY válida.")
    major, minor = raw[6], raw[7]
    if major == 1:
        if len(raw) < offset:
            raise ValueError("Cabeçalho NPY truncado.")
        header_len = struct.unpack("<H", raw[8:10])[0]
    elif major in (2, 3):
        if len(raw) < offset:
            raise ValueError("Cabeçalho NPY truncado.")
        header_len = struct.unpack("<I", raw[8:12])[0]
    else:
        raise ValueError(f"Versão NPY não suportada: {major}.{minor}")
    if header_len > MAX_HEADER or len(raw) < offset + header_len:
        raise ValueError("Cabeçalho NPY grande demais ou truncado.")
    header = ast.literal_eval(raw[offset:offset + header_len].decode("latin1").strip())
    return header, raw[offset + header_len:]


def inspect_payload(payload):
    counts = Counter()
    globals_seen = []
    first_ops = []
    for index, (opcode, arg, pos) in enumerate(pickletools.genops(payload)):
        counts[opcode.name] += 1
        if len(first_ops) < 30:
            first_ops.append({"op": opcode.name, "position": pos})
        if opcode.name in {"GLOBAL", "STACK_GLOBAL"}:
            globals_seen.append({"op": opcode.name, "arg": str(arg)[:200], "position": pos})
    return {
        "pickle_opcode_count": sum(counts.values()),
        "opcode_counts": dict(counts.most_common(30)),
        "global_references": globals_seen[:100],
        "first_opcodes": first_ops,
        "pickle_end_seen": "STOP" in counts,
        "safety": "pickletools apenas analisa opcodes; nenhum objeto é desserializado ou executado.",
    }


def inspect_bytes(raw, name):
    header, payload = split_npy(raw)
    descr = header.get("descr")
    result = {
        "file": name,
        "shape": header.get("shape"),
        "dtype": str(descr),
        "object_dtype": "O" in str(descr),
    }
    if not result["object_dtype"]:
        result["note"] = "Array numérico: não há payload pickle para inspecionar."
        return result
    if len(payload) > MAX_PAYLOAD:
        result["inspection_error"] = f"Payload maior que {MAX_PAYLOAD} bytes; análise interrompida."
        return result
    result.update(inspect_payload(payload))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="ZIP do dataset ou arquivo NPY individual")
    parser.add_argument("--member", help="Caminho interno exato do NPY quando a entrada é ZIP")
    parser.add_argument("--limit-mb", type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.limit_mb <= 64:
        raise SystemExit("--limit-mb deve ficar entre 1 e 64.")
    global MAX_PAYLOAD
    MAX_PAYLOAD = args.limit_mb * 1024 * 1024
    if not args.archive.is_file():
        raise SystemExit(f"Arquivo não encontrado: {args.archive}")
    try:
        if zipfile.is_zipfile(args.archive):
            if not args.member:
                raise SystemExit("Informe --member com o caminho exato do NPY dentro do ZIP.")
            with zipfile.ZipFile(args.archive) as zf:
                info = zf.getinfo(args.member)
                if info.file_size > MAX_PAYLOAD + MAX_HEADER + 12:
                    raise SystemExit("Membro excede o limite de inspeção.")
                with zf.open(info) as stream:
                    raw = stream.read(MAX_PAYLOAD + MAX_HEADER + 13)
            print(json.dumps(inspect_bytes(raw, args.member), ensure_ascii=False, indent=2))
        else:
            if args.member:
                raise SystemExit("--member só pode ser usado com ZIP.")
            if args.archive.stat().st_size > MAX_PAYLOAD + MAX_HEADER + 12:
                raise SystemExit("Arquivo excede o limite de inspeção.")
            print(json.dumps(inspect_bytes(args.archive.read_bytes(), str(args.archive)), ensure_ascii=False, indent=2))
    except (KeyError, OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"Falha na inspeção estática: {exc}")


if __name__ == "__main__":
    main()
