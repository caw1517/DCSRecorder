"""Check the necessary capture evidence for a take intended to deploy its gear.

This diagnoses missing recorded state; it cannot establish visible DCS rendering.
"""
import csv
import sys
from pathlib import Path


def check(path):
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("t,x,"))
    rows = list(csv.DictReader(line for line in lines[header:] if not line.startswith("END,")))
    print(f"{lines[0]}: {len(rows)} samples")
    for key in ("arg_0", "arg_3", "arg_5"):
        if key not in rows[0]:
            raise AssertionError(f"Recorded gear deployment unavailable: missing {key}")
        values = [float(row[key]) for row in rows]
        print(f"{key}: {min(values):.6f} .. {max(values):.6f}")
        assert max(values) > 0.9, f"{key}: no fully deployed gear in this take"


if __name__ == "__main__":
    check(sys.argv[1])
