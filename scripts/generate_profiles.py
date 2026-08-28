#!/usr/bin/env python3
from __future__ import annotations

import argparse
from factory import ROOT, load_toml, names, write_project


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", required=True)
    args = parser.parse_args()
    del args
    for profile in names("profiles"):
        meta = load_toml(ROOT / "profiles" / profile / "profile.toml")
        project = {
            "name": f"ChatGPT {profile.title()} Template",
            "slug": f"chatgpt-{profile}-template",
            "version": (ROOT / "VERSION").read_text().strip(),
            "profile": profile,
            "description": meta["description"],
            "overlays": [],
        }
        target = ROOT / "dist" / "templates" / profile
        manifest = write_project(project, target)
        print(f"generated {profile}: {len(manifest['files'])} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

