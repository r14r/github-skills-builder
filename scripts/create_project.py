#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from factory import FactoryError, ROOT, names, project_config, compose, write_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Codex-ready project templates")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-profiles")
    sub.add_parser("list-overlays")
    generate = sub.add_parser("generate")
    generate.add_argument("--config", required=True, type=Path)
    generate.add_argument("--output", type=Path)
    generate.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "list-profiles":
            print("\n".join(names("profiles")))
        elif args.command == "list-overlays":
            print("\n".join(names("overlays")))
        else:
            project = project_config(args.config)
            destination = args.output or ROOT / "dist" / "projects" / project["slug"]
            if args.dry_run:
                files, manifest = compose(project)
                print(json.dumps({"destination": str(destination), "files": sorted(files), "manifest": manifest}, indent=2))
            else:
                manifest = write_project(project, destination)
                print(f"generated {project['name']} at {destination} ({len(manifest['files'])} files)")
        return 0
    except FactoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

