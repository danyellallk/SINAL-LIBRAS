#!/usr/bin/env python3
"""Testes seguros do leitor de cabeçalho NPY do pacote contínuo UECE."""
import importlib.util
import io
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "inspect_uece_continuous_package",
    Path(__file__).with_name("inspect_uece_continuous_package.py"),
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def npy_header(dtype, shape):
    header = repr({
        "descr": dtype,
        "fortran_order": False,
        "shape": shape,
    }).encode("latin1")
    # NPY v1 header total (magic+version+length+header) must align to 16 bytes.
    padding = (-(10 + len(header) + 1)) % 16
    header += b" " * padding + b"\n"
    return b"\x93NUMPY" + bytes([1, 0]) + len(header).to_bytes(2, "little") + header


valid = module.read_npy_header(io.BytesIO(npy_header("<f4", (120, 318))))
assert valid["shape"] == (120, 318)
assert valid["dtype"] == "<f4"
assert valid["object_or_pickle_dtype"] is False

object_array = module.read_npy_header(io.BytesIO(npy_header("|O", (3,))))
assert object_array["object_or_pickle_dtype"] is True

invalid = module.read_npy_header(io.BytesIO(b"not-an-npy-file"))
assert "header_error" in invalid

print("OK: cabeçalhos numéricos, dtype objeto e arquivo inválido testados sem desserialização.")
