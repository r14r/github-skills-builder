from pathlib import Path
import tempfile
import unittest

from scripts.factory import ROOT, FactoryError, compose, names, project_config, validate, write_project


class FactoryTests(unittest.TestCase):
    def test_catalog(self):
        self.assertEqual(names("profiles"), ["application", "platform", "publishing"])
        self.assertIn("ai", names("overlays"))

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

    def test_rejects_forbidden_overlay(self):
        project = {
            "name": "Bad", "slug": "bad", "version": "0.0.0",
            "profile": "publishing", "description": "bad", "overlays": ["media"],
        }
        with self.assertRaises(FactoryError):
            compose(project)


if __name__ == "__main__":
    unittest.main()

