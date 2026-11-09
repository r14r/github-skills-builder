default:
    @just --list

profiles:
    python3 scripts/create_project.py list-profiles

overlays:
    python3 scripts/create_project.py list-overlays

generate-all:
    python3 scripts/generate_profiles.py --all

generate project:
    python3 scripts/create_project.py generate --config projects/{{project}}.toml

analyze path:
    python3 scripts/create_project.py analyze {{path}}

apply project target:
    python3 scripts/create_project.py apply --config projects/{{project}}.toml --target {{target}} --dry-run

test:
    python3 -m unittest discover -s tests -v

check:
    python3 -m unittest discover -s tests -v
    python3 scripts/generate_profiles.py --all

build: check
