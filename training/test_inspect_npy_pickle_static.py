#!/usr/bin/env python3
"""Testa a inspeção estática de pickle sem desserialização."""
import importlib.util
import pickle
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "inspect_npy_pickle_static",
    Path(__file__).with_name("inspect_npy_pickle_static.py"),
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_npy_object(payload, version=(1, 0)):
    header = repr({
        "descr": "|O",
        "fortran_order": False,
        "shape": (1,),
    }).encode("latin1")
    padding = (-(10 + len(header) + 1)) % 16
    header += b" " * padding + b"\n"
    return b"\x93NUMPY" + bytes([1, 0]) + len(header).to_bytes(2, "little") + header + payload


sample_pickle = pickle.dumps({"text": "sample", "values": [1, 2, 3]}, protocol=4)
result = module.inspect_bytes(make_npy_object(sample_pickle), "synthetic.npy")
assert result["object_dtype"] is True
assert result["pickle_opcode_count"] > 0
assert result["pickle_end_seen"] is True
assert "safety" in result

for version in ((2, 0), (3, 0)):
    version_result = module.inspect_bytes(make_npy_object(sample_pickle, version), f"synthetic-v{version[0]}.npy")
    assert version_result["pickle_end_seen"] is True

numeric_header = repr({
    "descr": "<f4",
    "fortran_order": False,
    "shape": (2, 3),
}).encode("latin1")
padding = (-(10 + len(numeric_header) + 1)) % 16
numeric_header += b" " * padding + b"\n"
numeric = b"\x93NUMPY" + bytes([1, 0]) + len(numeric_header).to_bytes(2, "little") + numeric_header + b"\x00" * 24
numeric_result = module.inspect_bytes(numeric, "numeric.npy")
assert numeric_result["object_dtype"] is False
assert "pickle_opcode_count" not in numeric_result

print("OK: NPY objeto analisado por opcodes; nenhum pickle foi desserializado.")

try:
    module.split_npy(b"\\x93NUMPY" + bytes([1, 0]) + b"\\x00")
except ValueError:
    pass
else:
    raise AssertionError("Cabeçalho truncado deveria ser rejeitado.")
