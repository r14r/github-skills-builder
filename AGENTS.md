# Repository Agent Instructions

## Purpose

Maintain the source-of-truth factory. Never edit generated files in `dist/` as
the primary implementation.

## Commands

- Generate all profiles: `python3 scripts/generate_profiles.py --all`
- Generate a project: `python3 scripts/create_project.py generate --config projects/<name>.toml`
- Validate: `python3 scripts/validate_project.py <output>`
- Test: `python3 -m unittest discover -s tests -v`

## Rules

- Use only the Python standard library in factory scripts.
- Keep merges deterministic: core, profile, overlays, then project variables.
- Undeclared file collisions are errors.
- Skills live below `.agents/skills/<skill-name>/SKILL.md`.
- Functional changes require tests and a semantic version update.

