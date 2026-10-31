
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex seo installer ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.package = self.root / "package with spaces"
        self.project = self.root / "project with spaces"
        self.home = self.root / "home"
        script = self.package / "scripts" / "install.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).resolve().parents[1] / "scripts" / "install.py", script)
        skill = self.package / "skills" / "seo" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: seo\ndescription: SEO analysis\n---\n")
        agent = self.package / "agents" / "seo-content.toml"
        agent.parent.mkdir(parents=True)
        agent.write_text('name = "seo-content"\n')
        self.skill_link = self.project / ".agents" / "skills" / "seo"
        self.agent_link = self.project / ".codex" / "agents" / "seo-content.toml"

    def run_install(self, *arguments, user=False, codex_home=None):
        env = dict(os.environ, HOME=str(self.home))
        env.pop("CODEX_HOME", None)
        if codex_home is not None:
            env["CODEX_HOME"] = str(codex_home)
        command = [sys.executable, str(self.package / "scripts" / "install.py")]
        command += ["--user"] if user else ["--project", str(self.project)]
        return subprocess.run(command + list(arguments), env=env, text=True, capture_output=True)

    def test_preview_creates_nothing(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["applied"])
        self.assertFalse(self.project.exists())

    def test_apply_installs_readable_links_and_is_idempotent(self):
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.skill_link.resolve(), self.package / "skills" / "seo")
        self.assertEqual(self.agent_link.read_text(), 'name = "seo-content"\n')
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({item["action"] for item in json.loads(result.stdout)["changes"]}, {"keep"})
        self.assertFalse((self.project / "AGENTS.md").exists())
        self.assertFalse((self.project / ".codex" / "config.toml").exists())

    def test_conflict_rejects_whole_plan_before_writing(self):
        self.agent_link.parent.mkdir(parents=True)
        self.agent_link.write_text("User agent\n")
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Nothing changed", result.stderr)
        self.assertFalse(self.skill_link.exists())
        self.assertEqual(self.agent_link.read_text(), "User agent\n")

    def test_broken_foreign_symlink_is_a_conflict(self):
        self.skill_link.parent.mkdir(parents=True)
        foreign = self.root / "absent foreign skill"
        self.skill_link.symlink_to(foreign)
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.skill_link.readlink(), foreign)
        self.assertFalse(self.agent_link.exists())

    def test_uninstall_preview_and_apply_preserve_unowned_files(self):
        self.assertEqual(self.run_install("--apply").returncode, 0)
        self.agent_link.unlink()
        self.agent_link.write_text("Replacement agent\n")
        foreign = self.skill_link.parent / "foreign"
        foreign.symlink_to(self.root / "missing")
        result = self.run_install("--uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.skill_link.is_symlink())
        result = self.run_install("--uninstall", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.skill_link.is_symlink())
        self.assertEqual(self.agent_link.read_text(), "Replacement agent\n")
        self.assertTrue(foreign.is_symlink())
        self.assertTrue(self.skill_link.parent.is_dir())

    def test_uninstall_removes_owned_links_when_source_was_removed(self):
        self.assertEqual(self.run_install("--apply").returncode, 0)
        shutil.rmtree(self.package / "skills" / "seo")
        result = self.run_install("--uninstall", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.skill_link.is_symlink())

    def test_user_scope_honours_codex_home_for_agents_only(self):
        codex_home = self.root / "other codex home"
        result = self.run_install("--apply", user=True, codex_home=codex_home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".agents" / "skills" / "seo").is_symlink())
        self.assertTrue((codex_home / "agents" / "seo-content.toml").is_symlink())
        self.assertFalse((self.home / ".codex").exists())

    def test_scope_is_required(self):
        result = subprocess.run(
            [sys.executable, str(self.package / "scripts" / "install.py")],
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
