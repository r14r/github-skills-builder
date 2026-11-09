# Architecture

The generator composes layers in this order:

1. `core/files`
2. `profiles/<profile>/files`
3. each `overlays/<overlay>/files` in declaration order
4. rendered project metadata
5. concatenated fragments

Normal files may not collide unless the later layer declares the relative path
in its `replace` list. `AGENTS.md` and `.env.example` are assembled from
fragments. Template files ending in `.tpl` are rendered using
`string.Template` and lose that suffix in the generated project.

Profiles describe broad repository shapes:

| Profile | Use |
|---|---|
| application | APIs, web apps, workers, CLIs |
| publishing | books, curricula, courses |
| platform | multi-application product suites |

Overlays add bounded capabilities without cloning a profile. The generated
`.template-manifest.json` records profile, overlays, variables, and files.

Each managed file also has a SHA-256 hash. The `apply` command uses these
hashes to distinguish unchanged generated content from user modifications.
Files that are not in the previous manifest are user-owned and are never
removed. Conflicting managed files require an explicit `--accept`; with
`--backup`, their previous content is copied below
`.template-backups/<timestamp>/` before replacement.

Application port variables are derived from `[ports].base`:

| Service | Offset | Default |
|---|---:|---:|
| Frontend | 000 | 60000 |
| Backend | 100 | 60100 |
| Database | 200 | 60200 |
| Redis | 300 | 60300 |
| Ollama | 434 | 60434 |

