#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from string import Template
import tomllib

ROOT = Path(__file__).resolve().parents[1]


class FactoryError(RuntimeError):
    pass


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def names(kind: str) -> list[str]:
    base = ROOT / kind
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith("."))


def project_config(path: Path) -> dict:
    data = load_toml(path)
    project = data.get("project", {})
    required = {"name", "slug", "profile", "version", "description"}
    missing = sorted(required - project.keys())
    if missing:
        raise FactoryError(f"missing project keys: {', '.join(missing)}")
    project.setdefault("overlays", [])
    return project


def variables(project: dict) -> dict[str, str]:
    return {
        "PROJECT_NAME": str(project["name"]),
        "PROJECT_SLUG": str(project["slug"]),
        "PROJECT_VERSION": str(project["version"]),
        "PROJECT_PROFILE": str(project["profile"]),
        "PROJECT_DESCRIPTION": str(project["description"]),
    }


def render(content: str, values: dict[str, str], source: Path) -> str:
    try:
        return Template(content).substitute(values)
    except KeyError as exc:
        raise FactoryError(f"{source}: unknown template variable {exc.args[0]}") from exc


def collect_files(layer: Path, values: dict[str, str], result: dict[str, bytes], origins: dict[str, str]) -> None:
    files = layer / "files"
    if not files.exists():
        return
    replace = set()
    metadata = layer / ("profile.toml" if layer.parent.name == "profiles" else "overlay.toml")
    if metadata.exists():
        replace = set(load_toml(metadata).get("replace", []))
    for source in sorted(p for p in files.rglob("*") if p.is_file()):
        relative = source.relative_to(files)
        output = relative.with_suffix("") if source.suffix == ".tpl" else relative
        key = output.as_posix()
        if key in result and key not in replace:
            raise FactoryError(f"file collision: {key} ({origins[key]} and {layer.relative_to(ROOT)})")
        raw = source.read_bytes()
        try:
            rendered = render(raw.decode(), values, source).encode()
        except UnicodeDecodeError:
            rendered = raw
        result[key] = rendered
        origins[key] = str(layer.relative_to(ROOT))


def compose(project: dict) -> tuple[dict[str, bytes], dict]:
    profile = project["profile"]
    overlays = project["overlays"]
    if profile not in names("profiles"):
        raise FactoryError(f"unknown profile: {profile}")
    profile_meta = load_toml(ROOT / "profiles" / profile / "profile.toml")
    allowed = set(profile_meta.get("allowed_overlays", []))
    unknown = [item for item in overlays if item not in names("overlays")]
    forbidden = [item for item in overlays if item not in allowed]
    if unknown:
        raise FactoryError(f"unknown overlays: {', '.join(unknown)}")
    if forbidden:
        raise FactoryError(f"overlays not allowed for {profile}: {', '.join(forbidden)}")

    values = variables(project)
    layers = [ROOT / "core", ROOT / "profiles" / profile]
    layers += [ROOT / "overlays" / item for item in overlays]
    output: dict[str, bytes] = {}
    origins: dict[str, str] = {}
    for layer in layers:
        collect_files(layer, values, output, origins)

    fragments: list[str] = []
    env_lines: dict[str, str] = {}
    skills: list[str] = []
    for layer in layers:
        agent = layer / "fragments" / "AGENTS.md"
        if agent.exists():
            fragments.append(render(agent.read_text(), values, agent).strip())
        env = layer / "fragments" / "env.example"
        if env.exists():
            for line in render(env.read_text(), values, env).splitlines():
                if not line or line.lstrip().startswith("#"):
                    continue
                key = line.split("=", 1)[0]
                if key in env_lines and env_lines[key] != line:
                    raise FactoryError(f"conflicting environment variable: {key}")
                env_lines[key] = line
        skill_root = layer / "skills"
        if skill_root.exists():
            for source in sorted(p for p in skill_root.rglob("*") if p.is_file()):
                rel = source.relative_to(skill_root)
                key = (Path(".agents/skills") / rel).as_posix()
                if key in output:
                    raise FactoryError(f"skill collision: {key}")
                output[key] = source.read_bytes()
                origins[key] = str(layer.relative_to(ROOT))
                if source.name == "SKILL.md":
                    skills.append(source.parent.name)

    output["AGENTS.md"] = ("\n\n".join(fragments) + "\n").encode()
    output[".env.example"] = ("\n".join(env_lines.values()) + "\n").encode()
    for directory in profile_meta.get("required_directories", []):
        output.setdefault(f"{directory}/.gitkeep", b"")

    manifest = {
        "schema": 1,
        "generator_version": (ROOT / "VERSION").read_text().strip(),
        "profile": profile,
        "overlays": overlays,
        "skills": sorted(set(skills)),
        "variables": values,
    }
    manifest["files"] = sorted(output)
    output[".template-manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return output, manifest


def write_project(project: dict, destination: Path, *, clean: bool = True) -> dict:
    files, manifest = compose(project)
    if clean and destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for relative, content in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return manifest


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    required = ["AGENTS.md", "PROJECT.md", "VERSION", ".env.example", ".template-manifest.json"]
    for name in required:
        if not (path / name).is_file():
            errors.append(f"missing file: {name}")
    manifest_path = path / ".template-manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            for name in manifest.get("files", []):
                if not (path / name).exists():
                    errors.append(f"manifest file missing: {name}")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid manifest: {exc}")
    skill_root = path / ".agents" / "skills"
    if skill_root.exists():
        for skill in skill_root.iterdir():
            if skill.is_dir() and not (skill / "SKILL.md").is_file():
                errors.append(f"skill missing SKILL.md: {skill.name}")
    return errors

