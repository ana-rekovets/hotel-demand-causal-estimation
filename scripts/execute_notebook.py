#!/usr/bin/env python3
"""Execute a notebook end to end and write the result with its outputs.

Usage:
    python scripts/execute_notebook.py input.ipynb output.ipynb

Runs with a generous timeout because the Part 2 simulation takes roughly 40
minutes. Errors are not swallowed: if a cell raises, execution stops and this
script exits non-zero, so a broken notebook fails the build rather than
silently producing a notebook with a traceback in it.
"""

from __future__ import annotations

import os
import sys

import nbformat
from nbclient import NotebookClient


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    src, dst = sys.argv[1], sys.argv[2]
    timeout = int(os.environ.get("NB_TIMEOUT", "10800"))  # 3 hours

    nb = nbformat.read(src, as_version=4)
    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": os.getcwd()}},
        allow_errors=False,
    )
    print(f"executing {src} (timeout {timeout}s, cwd {os.getcwd()})", flush=True)
    client.execute()
    nbformat.write(nb, dst)
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
