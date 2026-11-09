#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from factory import (
    FactoryError, ROOT, analyze_project, apply_project, compose, names,
    project_config, write_project,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Codex-ready project templates")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-profiles")
    sub.add_parser("list-overlays")
    generate = sub.add_parser("generate")
    generate.add_argument("--config", required=True, type=Path)
    generate.add_argument("--output", type=Path)
    generate.add_argument("--dry-run", action="store_true")
    analyze = sub.add_parser("analyze")
    analyze.add_argument("path", type=Path)
    apply = sub.add_parser("apply")
    apply.add_argument("--config", required=True, type=Path)
    apply.add_argument("--target", required=True, type=Path)
    apply.add_argument("--dry-run", action="store_true")
    apply.add_argument("--accept", action="store_true")
    apply.add_argument("--backup", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "list-profiles":
            print("\n".join(names("profiles")))
        elif args.command == "list-overlays":
            print("\n".join(names("overlays")))
        elif args.command == "analyze":
            print(json.dumps(analyze_project(args.path), indent=2))
        elif args.command == "apply":
            project = project_config(args.config)
            plan = apply_project(
                project, args.target, dry_run=args.dry_run,
                accept=args.accept, backup=args.backup,
            )
            print(json.dumps(plan, indent=2))
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

