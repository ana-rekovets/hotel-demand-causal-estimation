#!/usr/bin/env python3
"""Compare the numeric outputs of two runs of the same notebook.

Re-executing a notebook should reproduce its committed results exactly when the
analysis is properly seeded. This script checks that, comparing cell output
text between two .ipynb files while ignoring the things that legitimately
differ between runs: wall-clock timings, progress bars, memory addresses and
object reprs.

Usage:
    python scripts/compare_notebook_results.py committed.ipynb rerun.ipynb

Exit 0 = the two runs agree on every number.
Exit 1 = they disagree; the differing cells and values are printed.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

# Patterns whose content varies run to run without indicating a real difference.
NOISE = [
    re.compile(r"\(?\b\d+\.\d+\s*s\b\)?"),          # "47.1s", "(0.34s)"
    re.compile(r"\bTotal:\s*[\d.]+s"),               # "Total: 303.9s"
    re.compile(r"\bin\s+[\d.]+s\b"),                 # "in 0.41s"
    re.compile(r"0x[0-9a-fA-F]+"),                   # memory addresses
    re.compile(r"<[\w.]+ (?:object|at) [^>]*>"),     # object reprs
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),     # clock times
    re.compile(r"\bELAPSED\b.*"),
    re.compile(r"\r"),
    re.compile(r"\x1b\[[0-9;]*m"),                   # ANSI colour
    re.compile(r"[─━]{2,}"),                         # progress bars / rules
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:MB|GB|KB)/s\b"),
    re.compile(r"eta\s+\d+:\d+:\d+"),
]

NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def scrub(text: str) -> str:
    for pat in NOISE:
        text = pat.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def cell_outputs(path: pathlib.Path) -> list[str]:
    nb = json.loads(path.read_text())
    out: list[str] = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        parts: list[str] = []
        for o in cell.get("outputs", []):
            if "text" in o:
                parts.append("".join(o["text"]))
            data = o.get("data", {})
            if "text/plain" in data:
                parts.append("".join(data["text/plain"]))
        out.append(scrub("\n".join(parts)))
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    a_path, b_path = (pathlib.Path(p) for p in sys.argv[1:3])
    a, b = cell_outputs(a_path), cell_outputs(b_path)

    print(f"committed : {a_path}  ({len(a)} code cells)")
    print(f"re-run    : {b_path}  ({len(b)} code cells)")

    if len(a) != len(b):
        print(f"\nFAIL: different number of code cells ({len(a)} vs {len(b)})")
        return 1

    problems = 0
    total_nums = 0
    for i, (x, y) in enumerate(zip(a, b)):
        nx, ny = NUM.findall(x), NUM.findall(y)
        total_nums += len(nx)
        if nx == ny:
            continue
        problems += 1
        print(f"\n--- cell {i}: numeric outputs differ ---")
        if len(nx) != len(ny):
            print(f"    count {len(nx)} vs {len(ny)}")
        shown = 0
        for j, (p, q) in enumerate(zip(nx, ny)):
            if p != q:
                print(f"    [{j}] committed={p}  rerun={q}")
                shown += 1
                if shown >= 12:
                    print("    ... (further differences suppressed)")
                    break

    print(f"\ncompared {total_nums} numbers across {len(a)} code cells")
    if problems:
        print(f"FAIL: {problems} cell(s) differ between runs.")
        return 1
    print("OK: the re-run reproduces every number in the committed outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
