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


def make_npy(payload, descr="|O", version=(1, 0), shape=(1,)):
    header = repr({
        "descr": descr,
        "fortran_order": False,
        "shape": shape,
    }).encode("latin1")
    prefix_size = 10 if version == (1, 0) else 12
    header += b" " * (-(prefix_size + len(header) + 1) % 16) + b"\n"
    length_size = 2 if version == (1, 0) else 4
    length = len(header).to_bytes(length_size, "little")
    return b"\x93NUMPY" + bytes(version) + length + header + payload


sample_pickle = pickle.dumps({"text": "sample", "values": [1, 2, 3]}, protocol=4)
for version in ((1, 0), (2, 0), (3, 0)):
    result = module.inspect_bytes(make_npy(sample_pickle, version=version), f"synthetic-v{version[0]}.npy")
    assert result["object_dtype"] is True
    assert result["pickle_opcode_count"] > 0
    assert result["pickle_end_seen"] is True
    assert "safety" in result

numeric = make_npy(b"\x00" * 24, descr="<f4", shape=(2, 3))
numeric_result = module.inspect_bytes(numeric, "numeric.npy")
assert numeric_result["object_dtype"] is False
assert "pickle_opcode_count" not in numeric_result

try:
    module.split_npy(b"\x93NUMPY" + bytes([1, 0]) + b"\x00")
except ValueError:
    pass
else:
    raise AssertionError("Cabeçalho truncado deveria ser rejeitado.")

print("OK: NPY v1/v2/v3 e cabeçalho truncado; nenhum pickle foi desserializado.")
