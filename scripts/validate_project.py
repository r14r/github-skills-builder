#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from factory import validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate(args.path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

