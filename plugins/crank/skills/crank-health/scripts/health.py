#!/usr/bin/env python3
"""crank-health's scanner. `python3 health.py --help` lists the commands."""

import sys

if sys.version_info < (3, 11):
    sys.exit(
        f"health.py needs Python 3.11 or newer; this is {sys.version.split()[0]}. "
        "Run it as: uv run --python 3.12 health.py …"
    )

from healthlib.cli import main

if __name__ == "__main__":
    sys.exit(main())
