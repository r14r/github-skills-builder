# GitHub Skills Builder

Factory for generating Codex-ready GitHub project templates from a shared core,
one profile, and optional overlays.

## Quick start

```bash
python3 scripts/create_project.py list-profiles
python3 scripts/create_project.py list-overlays
python3 scripts/generate_profiles.py --all
python3 scripts/create_project.py generate --config projects/ai-task-studio.toml
python3 -m unittest discover -s tests -v
```

Generated output is written below `dist/` and is intentionally not versioned.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for composition rules.

