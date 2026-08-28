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

