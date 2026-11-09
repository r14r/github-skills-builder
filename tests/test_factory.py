from pathlib import Path
import tempfile
import unittest

from scripts.factory import (
    ROOT,
    FactoryError,
    analyze_project,
    apply_project,
    compose,
    names,
    project_config,
    validate,
    write_project,
)


class FactoryTests(unittest.TestCase):
    def test_catalog(self):
        self.assertEqual(names("profiles"), ["application", "platform", "publishing"])
        self.assertIn("ai", names("overlays"))
        self.assertIn("fastapi-nuxt", names("overlays"))

    def test_generate_all_presets(self):
        for config in sorted((ROOT / "projects").glob("*.toml")):
            project = project_config(config)
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / project["slug"]
                manifest = write_project(project, target)
                self.assertEqual(validate(target), [])
                self.assertEqual(manifest["profile"], project["profile"])
                self.assertTrue((target / ".agents/skills/project-bootstrap/SKILL.md").exists())

    def test_ai_overlay_merges_environment(self):
        project = project_config(ROOT / "projects/ai-task-studio.toml")
        files, _ = compose(project)
        env = files[".env.example"].decode()
        self.assertIn("OLLAMA_BASE_URL=", env)
        self.assertEqual(env.count("OLLAMA_BASE_URL="), 1)
        self.assertIn("FRONTEND_PORT=60000", env)
        self.assertIn("BACKEND_PORT=60100", env)
        self.assertIn("OLLAMA_PORT=60434", env)

    def test_fastapi_nuxt_skeleton_is_runnable_shape(self):
        project = project_config(ROOT / "projects/media-studio.toml")
        files, manifest = compose(project)
        self.assertIn("compose.yaml", files)
        self.assertIn("backend/app/main.py", files)
        self.assertIn("frontend/app/pages/index.vue", files)
        self.assertIn(".agents/skills/fullstack-feature/SKILL.md", files)
        self.assertEqual(manifest["schema"], 2)
        self.assertRegex(manifest["files"]["backend/app/main.py"], r"^[0-9a-f]{64}$")

    def test_analyze_recommends_profile_and_overlays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "backend").mkdir()
            (root / "backend/pyproject.toml").write_text("dependencies = ['fastapi']")
            (root / "nuxt.config.ts").write_text("export default defineNuxtConfig({})")
            (root / "compose.yaml").write_text("services: {}")
            report = analyze_project(root)
            self.assertEqual(report["profile"], "application")
            self.assertIn("fastapi-nuxt", report["recommended_overlays"])
            self.assertEqual(report["compose_files"], ["compose.yaml"])

    def test_analyze_reads_configuration_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                'dependencies = ["fastapi", "langchain", "asyncpg"]'
            )
            report = analyze_project(root)
            self.assertIn("fastapi-nuxt", report["recommended_overlays"])
            self.assertIn("ai", report["recommended_overlays"])
            self.assertNotIn("task-orchestration", report["recommended_overlays"])

    def test_apply_preserves_user_files_and_detects_conflicts(self):
        project = project_config(ROOT / "projects/media-studio.toml")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            first = apply_project(project, target)
            self.assertTrue(first["create"])
            (target / "user-notes.md").write_text("keep me")
            (target / "PROJECT.md").write_text("user edit")
            plan = apply_project(project, target, dry_run=True)
            self.assertIn("PROJECT.md", plan["conflicts"])
            self.assertIn("user-notes.md", plan["preserved"])
            with self.assertRaises(FactoryError):
                apply_project(project, target)
            apply_project(project, target, accept=True, backup=True)
            backups = list((target / ".template-backups").rglob("PROJECT.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), "user edit")
            self.assertEqual((target / "user-notes.md").read_text(), "keep me")

    def test_custom_port_base(self):
        project = project_config(ROOT / "projects/sql-learning-studio.toml")
        files, _ = compose(project)
        env = files[".env.example"].decode()
        self.assertIn("APP_PORT=61000", env)
        self.assertIn("MYSQL_PORT=61200", env)

    def test_rejects_forbidden_overlay(self):
        project = {
            "name": "Bad", "slug": "bad", "version": "0.0.0",
            "profile": "publishing", "description": "bad", "overlays": ["media"],
        }
        with self.assertRaises(FactoryError):
            compose(project)


if __name__ == "__main__":
    unittest.main()

