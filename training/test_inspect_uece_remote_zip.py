#!/usr/bin/env python3
"""Testa o parser de cabeçalho NPY usado na inspeção remota."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "inspect_uece_remote_zip",
    Path(__file__).with_name("inspect_uece_remote_zip.py"),
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_header(version, dtype="<f4", shape=(4, 318)):
    h = repr({"descr": dtype, "fortran_order": False, "shape": shape}).encode("latin1")
    offset = 10 if version == (1, 0) else 12
    h += b" " * (-(offset + len(h) + 1) % 16) + b"\n"
    n = 2 if version == (1, 0) else 4
    return b"\x93NUMPY" + bytes(version) + len(h).to_bytes(n, "little") + h


for version in ((1, 0), (2, 0), (3, 0)):
    result = module.npy_header(make_header(version))
    assert result["shape"] == (4, 318)
    assert result["object_dtype"] is False

obj = module.npy_header(make_header((1, 0), dtype="|O", shape=(1,)))
assert obj["object_dtype"] is True
assert "header_error" in module.npy_header(b"not npy")
print("OK: cabeçalhos NPY v1/v2/v3, dtype objeto e arquivo inválido.")
