#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
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
    project = dict(data.get("project", {}))
    required = {"name", "slug", "profile", "version", "description"}
    missing = sorted(required - project.keys())
    if missing:
        raise FactoryError(f"missing project keys: {', '.join(missing)}")
    project.setdefault("overlays", [])
    project["_config"] = {key: value for key, value in data.items() if key != "project"}
    return project


def variables(project: dict) -> dict[str, str]:
    config = project.get("_config", {})
    ports = config.get("ports", {})
    base = int(ports.get("base", 60000))
    values = {
        "PROJECT_NAME": str(project["name"]),
        "PROJECT_SLUG": str(project["slug"]),
        "PROJECT_VERSION": str(project["version"]),
        "PROJECT_PROFILE": str(project["profile"]),
        "PROJECT_DESCRIPTION": str(project["description"]),
        "BASE_PORT": str(base),
        "FRONTEND_PORT": str(ports.get("frontend", base)),
        "BACKEND_PORT": str(ports.get("backend", base + 100)),
        "DATABASE_PORT": str(ports.get("database", base + 200)),
        "REDIS_PORT": str(ports.get("redis", base + 300)),
        "OLLAMA_PORT": str(ports.get("ollama", base + 434)),
    }
    application = config.get("application", {})
    values["PYTHON_VERSION"] = str(application.get("python_version", "3.12"))
    values["NODE_VERSION"] = str(application.get("node_version", "22"))
    values["DATABASE_NAME"] = str(application.get("database_name", project["slug"].replace("-", "_")))
    return values


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
        "schema": 2,
        "generator_version": (ROOT / "VERSION").read_text().strip(),
        "profile": profile,
        "overlays": overlays,
        "skills": sorted(set(skills)),
        "variables": values,
    }
    manifest["files"] = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in sorted(output.items())
    }
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
            files = manifest.get("files", {})
            names_in_manifest = files if isinstance(files, dict) else files
            for name in names_in_manifest:
                if not (path / name).exists():
                    errors.append(f"manifest file missing: {name}")
            if isinstance(files, dict):
                for name, expected in files.items():
                    target = path / name
                    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                        errors.append(f"managed file modified: {name}")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid manifest: {exc}")
    skill_root = path / ".agents" / "skills"
    if skill_root.exists():
        for skill in skill_root.iterdir():
            if skill.is_dir() and not (skill / "SKILL.md").is_file():
                errors.append(f"skill missing SKILL.md: {skill.name}")
    return errors


def apply_project(
    project: dict,
    target: Path,
    *,
    dry_run: bool = False,
    accept: bool = False,
    backup: bool = False,
) -> dict:
    generated, manifest = compose(project)
    old_manifest_path = target / ".template-manifest.json"
    old_hashes: dict[str, str] = {}
    if old_manifest_path.exists():
        old = json.loads(old_manifest_path.read_text())
        if isinstance(old.get("files"), dict):
            old_hashes = old["files"]

    plan = {"create": [], "update": [], "unchanged": [], "conflicts": [], "preserved": []}
    for relative, content in sorted(generated.items()):
        destination = target / relative
        desired_hash = hashlib.sha256(content).hexdigest()
        if not destination.exists():
            plan["create"].append(relative)
        elif destination.is_file() and hashlib.sha256(destination.read_bytes()).hexdigest() == desired_hash:
            plan["unchanged"].append(relative)
        elif relative in old_hashes and destination.is_file() and hashlib.sha256(destination.read_bytes()).hexdigest() == old_hashes[relative]:
            plan["update"].append(relative)
        else:
            plan["conflicts"].append(relative)

    if target.exists():
        managed = set(old_hashes) | set(generated)
        plan["preserved"] = sorted(
            p.relative_to(target).as_posix()
            for p in target.rglob("*")
            if p.is_file()
            and p.relative_to(target).as_posix() not in managed
            and ".template-backups" not in p.parts
        )
    if dry_run:
        return plan
    if plan["conflicts"] and not accept:
        raise FactoryError("apply conflicts: " + ", ".join(plan["conflicts"]))

    backup_root = None
    if backup and plan["conflicts"]:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_root = target / ".template-backups" / stamp
    target.mkdir(parents=True, exist_ok=True)
    for relative in plan["create"] + plan["update"] + (plan["conflicts"] if accept else []):
        destination = target / relative
        if backup_root and destination.exists():
            copy = backup_root / relative
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, copy)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(generated[relative])
    (target / ".template-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return plan


def analyze_project(path: Path) -> dict:
    if not path.is_dir():
        raise FactoryError(f"not a directory: {path}")
    files = {
        p.relative_to(path).as_posix().lower()
        for p in path.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    text_suffixes = {
        ".json", ".md", ".py", ".toml", ".ts", ".vue", ".yaml", ".yml",
    }
    content_parts = [*sorted(files)]
    for source in path.rglob("*"):
        if (
            source.is_file()
            and source.suffix.lower() in text_suffixes
            and ".git" not in source.parts
            and source.stat().st_size <= 256_000
        ):
            try:
                content_parts.append(source.read_text(errors="ignore").lower())
            except OSError:
                pass
    joined = "\n".join(content_parts)
    profile = "application"
    reasons: list[str] = []
    if any(name.startswith(("content/", "chapters/", "exercises/")) for name in files):
        profile = "publishing"
        reasons.append("publishing content directories detected")
    if any(name.startswith(("apps/", "services/", "packages/", "products/")) for name in files):
        profile = "platform"
        reasons.append("multi-application platform directories detected")
    overlays: list[str] = []
    checks = [
        ("fastapi-nuxt", ("fastapi", "nuxt.config", "package.json")),
        ("ai", ("config/ai/", "ollama", "langchain", "openai")),
        ("streamlit", ("streamlit",)),
        ("media", ("ffmpeg", "media")),
        ("kubernetes", ("kubernetes", "k8s", "helm")),
        ("cli", ("cmd/", "cobra", "argparse")),
        ("task-orchestration", ("scheduler", "celery", "apscheduler")),
        ("update-cli", ("update-cli.yaml",)),
        ("multi-database", ("postgres", "mysql", "sqlite")),
    ]
    for overlay, needles in checks:
        if any(needle in joined for needle in needles):
            overlays.append(overlay)
    compose_files = sorted(name for name in files if Path(name).name in {"compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"})
    missing = [
        name for name in ("AGENTS.md", ".env.example", "VERSION")
        if name.lower() not in files
    ]
    return {
        "path": str(path.resolve()),
        "profile": profile,
        "recommended_overlays": overlays,
        "compose_files": compose_files,
        "missing_baseline_files": missing,
        "reasons": reasons or ["application structure is the best match"],
    }

