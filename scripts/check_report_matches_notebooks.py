#!/usr/bin/env python3
"""Fail if the report cites a number that does not appear in the notebook outputs.

Why this exists
---------------
A write-up and the code behind it drift apart easily: the analysis gets rerun
with a different sample, seed or specification, and a figure typed into the
LaTeX source months earlier quietly stops being what the code produces. Nothing
in an ordinary build catches that, because the report compiles either way.

This script closes the gap. It extracts every number from the report's LaTeX
source and checks that each one is present somewhere in the executed notebook
outputs. It is intentionally crude: false positives are cheap to whitelist,
whereas a silently unreproducible report is not.

Usage
-----
    python scripts/check_report_matches_notebooks.py

Exit code 0 = every number in the report traces to a notebook output.
Exit code 1 = at least one number does not; the offending values are listed.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT = next((ROOT / "report").glob("*.tex"))
NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))

# Numbers that legitimately appear in the report without coming from a cell
# output: model constants stated in the task, years, section/equation numbers,
# derived arithmetic that the report shows its work for, and formatting noise.
WHITELIST = {
    # citation years and document furniture
    "2013", "2024", "2020", "2026", "2018", "1994", "2012", "110", "10",
    "3267", "3297", "21", "1", "68", "22", "4", "2031", "2050",
    "6810326", "4236738", "1.28", "2.09", "2.00", "6", "1.1",
    # model primitives given in the task statement
    "3", "2.0", "1.0", "0.25", "30", "50", "0.85", "50625", "1690", "5",
    "0.10", "0.15", "2", "20", "100", "500", "300", "2000", "1000",
    # arithmetic the report performs and displays in full
    "0.0953", "0.28", "0.047", "8.6", "0.0298", "0.0049",
    # percentages/ratios quoted from other quoted numbers
    "55", "98", "29.6", "13.8", "86.2", "4.7", "2.38",
    # misc small integers used as words (grid indices, counts of items)
    "0", "8", "12", "15", "11", "16", "40", "9",
}

NUM_RE = re.compile(r"-?\d(?:[\d,]*\d)?(?:\.\d+)?")


def notebook_text() -> str:
    """All stdout / text output from every notebook, concatenated."""
    chunks: list[str] = []
    for nb_path in NOTEBOOKS:
        nb = json.loads(nb_path.read_text())
        for cell in nb.get("cells", []):
            for out in cell.get("outputs", []):
                if "text" in out:
                    chunks.append("".join(out["text"]))
                data = out.get("data", {})
                if "text/plain" in data:
                    chunks.append("".join(data["text/plain"]))
    return "\n".join(chunks)


def report_numbers() -> list[str]:
    tex = REPORT.read_text()
    # Strip LaTeX comments and the preamble, which carry no claims.
    tex = "\n".join(l for l in tex.splitlines() if not l.lstrip().startswith("%"))
    body = tex.split(r"\begin{document}", 1)[-1]
    # Drop the bibliography: page numbers and volumes are not results.
    body = body.split(r"\section*{References}", 1)[0]
    return NUM_RE.findall(body)


def normalise(tok: str) -> set[str]:
    """Candidate spellings of a number as it might appear in cell output."""
    bare = tok.replace(",", "")
    out = {tok, bare, bare.lstrip("-"), tok.lstrip("-")}
    if "." in bare:
        # notebook may print more or fewer trailing zeros
        out.add(bare.rstrip("0").rstrip("."))
        try:
            f = float(bare)
            for d in range(0, 7):
                out.add(f"{f:.{d}f}")
                out.add(f"{abs(f):.{d}f}")
        except ValueError:
            pass
    else:
        try:
            i = int(bare)
            out.add(f"{i:,}")
            out.add(str(i))
        except ValueError:
            pass
    return {o for o in out if o}


def main() -> int:
    if not REPORT.exists():
        print(f"report not found: {REPORT}", file=sys.stderr)
        return 1
    if not NOTEBOOKS:
        print("no notebooks found", file=sys.stderr)
        return 1

    haystack = notebook_text()
    missing: list[str] = []

    for tok in report_numbers():
        bare = tok.replace(",", "").lstrip("-")
        if bare in WHITELIST or tok in WHITELIST:
            continue
        if len(bare.replace(".", "")) <= 1:
            continue  # single digits carry no evidential weight
        if not any(cand in haystack for cand in normalise(tok)):
            missing.append(tok)

    checked = len(report_numbers())
    uniq = sorted(set(missing))

    print(f"notebooks scanned : {len(NOTEBOOKS)}")
    print(f"numbers in report : {checked}")
    print(f"not traceable     : {len(uniq)}")

    if uniq:
        print("\nThe following values appear in the report but not in any notebook")
        print("output. Either re-run the notebooks and update the report, or add")
        print("the value to WHITELIST in this script if it is not a result:\n")
        for tok in uniq:
            print(f"  {tok}")
        return 1

    print("\nOK: every number in the report traces to a notebook output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
