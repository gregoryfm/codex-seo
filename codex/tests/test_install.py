
import json
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


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
        self.agent_file = self.project / ".codex" / "agents" / "seo-content.toml"
        self.receipt = self.project / ".codex" / "agents" / ".codex-seo-managed-agents.json"

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

    def test_apply_links_skills_copies_agents_and_is_idempotent(self):
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.skill_link.resolve(), self.package / "skills" / "seo")
        self.assertFalse(self.agent_file.is_symlink())
        self.assertEqual(self.agent_file.read_text(), 'name = "seo-content"\n')
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt["agents"]["seo-content.toml"]["source"], str((self.package / "agents" / "seo-content.toml").resolve()))
        self.assertEqual(len(receipt["agents"]["seo-content.toml"]["installed_sha256"]), 64)
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({item["action"] for item in json.loads(result.stdout)["changes"]}, {"keep"})
        self.assertFalse((self.project / "AGENTS.md").exists())
        self.assertFalse((self.project / ".codex" / "config.toml").exists())

    def test_conflict_rejects_whole_plan_before_writing(self):
        self.agent_file.parent.mkdir(parents=True)
        self.agent_file.write_text("User agent\n")
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Nothing changed", result.stderr)
        self.assertFalse(self.skill_link.exists())
        self.assertEqual(self.agent_file.read_text(), "User agent\n")
        self.assertFalse(self.receipt.exists())

    def test_broken_foreign_symlink_is_a_conflict(self):
        self.skill_link.parent.mkdir(parents=True)
        foreign = self.root / "absent foreign skill"
        self.skill_link.symlink_to(foreign)
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.skill_link.readlink(), foreign)
        self.assertFalse(self.agent_file.exists())

    def test_uninstall_preview_and_apply_preserve_user_edits_and_foreign_links(self):
        self.assertEqual(self.run_install("--apply").returncode, 0)
        self.agent_file.write_text("Replacement agent\n")
        foreign = self.skill_link.parent / "foreign"
        foreign.symlink_to(self.root / "missing")
        result = self.run_install("--uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.skill_link.is_symlink())
        result = self.run_install("--uninstall", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.skill_link.is_symlink())
        self.assertEqual(self.agent_file.read_text(), "Replacement agent\n")
        self.assertFalse(self.receipt.exists())
        self.assertTrue(foreign.is_symlink())
        self.assertTrue(self.skill_link.parent.is_dir())

    def test_uninstall_removes_owned_links_when_source_was_removed(self):
        self.assertEqual(self.run_install("--apply").returncode, 0)
        shutil.rmtree(self.package / "skills" / "seo")
        result = self.run_install("--uninstall", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.skill_link.is_symlink())
        self.assertFalse(self.agent_file.exists())
        self.assertFalse(self.receipt.exists())

    def test_migrates_old_same_source_agent_link_to_regular_copy(self):
        self.agent_file.parent.mkdir(parents=True)
        self.agent_file.symlink_to(self.package / "agents" / "seo-content.toml")
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.agent_file.is_symlink())
        self.assertEqual(self.agent_file.read_text(), 'name = "seo-content"\n')
        self.assertTrue(self.receipt.is_file())

    def test_refreshes_receipt_owned_copy_after_source_change(self):
        self.assertEqual(self.run_install("--apply").returncode, 0)
        source = self.package / "agents" / "seo-content.toml"
        source.write_text('name = "seo-content"\ndescription = "updated"\n')
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.agent_file.read_text(), source.read_text())
        self.assertEqual(json.loads(result.stdout)["changes"][-1]["action"], "refresh")

    def test_preserves_user_edited_receipt_owned_copy_on_refresh(self):
        self.assertEqual(self.run_install("--apply").returncode, 0)
        self.agent_file.write_text("User edit\n")
        source = self.package / "agents" / "seo-content.toml"
        source.write_text('name = "seo-content"\ndescription = "updated"\n')
        result = self.run_install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.agent_file.read_text(), "User edit\n")
        self.assertEqual(json.loads(result.stdout)["changes"][-1]["action"], "preserve")
        self.assertTrue(self.receipt.exists())
        result = self.run_install("--uninstall", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.agent_file.read_text(), "User edit\n")
        self.assertFalse(self.receipt.exists())

    def test_receipt_write_failure_rolls_back_new_files(self):
        spec = importlib.util.spec_from_file_location("codex_seo_installer", self.package / "scripts" / "install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        changes, receipt_raw, desired_receipt, receipt_path, _ = installer.install_plan(
            self.package, self.project, self.project / ".codex"
        )
        with mock.patch.object(installer, "atomic_write", side_effect=OSError("simulated receipt failure")):
            with self.assertRaisesRegex(OSError, "simulated receipt failure"):
                installer.apply_install(self.package, changes, receipt_path, receipt_raw, desired_receipt)
        self.assertFalse(self.project.exists())

    def test_refresh_preserves_an_edit_saved_after_planning(self):
        self.assertEqual(self.run_install("--apply").returncode, 0)
        spec = importlib.util.spec_from_file_location("codex_seo_installer", self.package / "scripts" / "install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        source = self.package / "agents" / "seo-content.toml"
        source.write_text('name = "seo-content"\ndescription = "Updated source"\n')
        changes, receipt_raw, desired_receipt, receipt_path, _ = installer.install_plan(
            self.package, self.project, self.project / ".codex"
        )
        edited = 'name = "seo-content"\ndescription = "User edit"\n'
        self.agent_file.write_text(edited)
        with self.assertRaisesRegex(ValueError, "changed during installation"):
            installer.apply_install(self.package, changes, receipt_path, receipt_raw, desired_receipt)
        self.assertEqual(self.agent_file.read_text(), edited)
        self.assertEqual(self.receipt.read_bytes(), receipt_raw)

    def test_user_scope_honours_codex_home_for_agents_only(self):
        codex_home = self.root / "other codex home"
        result = self.run_install("--apply", user=True, codex_home=codex_home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".agents" / "skills" / "seo").is_symlink())
        self.assertFalse((codex_home / "agents" / "seo-content.toml").is_symlink())
        self.assertTrue((codex_home / "agents" / "seo-content.toml").is_file())
        self.assertFalse((self.home / ".codex").exists())

    def test_scope_is_required(self):
        result = subprocess.run(
            [sys.executable, str(self.package / "scripts" / "install.py")],
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
