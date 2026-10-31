from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]


class PortTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex seo test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {**os.environ, 'CODEX_SEO_DATA_DIR': str(self.root / 'runtime data'), 'PYTHONDONTWRITEBYTECODE': '1'}

    def command(self, *args):
        return subprocess.run([sys.executable, str(PACKAGE / 'scripts/codex-seo.py'), *args], env=self.env, capture_output=True, text=True)

    def test_doctor_is_read_only_and_reports_unready(self):
        result = self.command('doctor', '--json')
        self.assertEqual(result.returncode, 3, result.stderr)
        status = json.loads(result.stdout)
        self.assertFalse(status['ready'])
        self.assertFalse(status['browser_ready'])
        self.assertFalse((self.root / 'runtime data').exists())
        self.assertNotIn(str(self.root), result.stdout)

    def test_invalid_script_rejected_before_setup(self):
        for script in ('../fetch_page.py', 'release_sign.py', '/tmp/fetch_page.py'):
            result = self.command('run', script)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((self.root / 'runtime data').exists())

    def test_missing_runtime_does_not_install_dependencies(self):
        result = self.command('run', 'fetch_page.py', 'https://example.com')
        self.assertEqual(result.returncode, 3)
        self.assertFalse((self.root / 'runtime data').exists())

    def test_unsafe_runtime_root_rejected(self):
        self.env['CODEX_SEO_DATA_DIR'] = '/'
        self.assertEqual(self.command('doctor', '--json').returncode, 2)

    def test_source_mutation_and_claude_setup_are_disabled(self):
        for args in (('run', 'sync_flow.py'), ('run', '--', 'sync_flow.py'), ('run', '--extension=banana', 'setup_mcp.py'), ('run', '--extension', 'banana', 'setup_mcp.py', '--key', 'never-use-a-real-key')):
            result = self.command(*args)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((self.root / 'runtime data').exists())

    def test_explicit_schema_validator_accepts_json_and_html(self):
        value = {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'Example </script> Company'}
        target = self.root / 'schema.json'
        target.write_text(json.dumps(value))
        result = self.command('validate-schema', str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['valid'])
        html = self.root / 'page.html'
        html.write_text('<script type="application/ld+json">' + json.dumps({**value, 'name': 'Example Company'}) + '</script>')
        self.assertEqual(self.command('validate-schema', str(html)).returncode, 0)

    def test_schema_issues_are_not_silently_skipped(self):
        for value in ({'@context': 'https://schema.org', '@type': 'Organization', 'name': '[Business Name]'}, {'@type': 'Organization'}):
            target = self.root / 'schema.jsonld'
            target.write_text(json.dumps(value))
            result = self.command('validate-schema', str(target))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)['valid'])
            self.assertTrue(json.loads(result.stdout)['issues'])

    def test_schema_multitype_checks_each_type(self):
        target = self.root / 'multitype.json'
        target.write_text(json.dumps({'@context': 'https://schema.org', '@type': ['Organization', 'Corporation']}))
        result = self.command('validate-schema', str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['valid'])
        target.write_text(json.dumps({'@context': 'https://schema.org', '@type': ['Organization', 'HowTo']}))
        result = self.command('validate-schema', str(target))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue(any('HowTo' in issue for issue in json.loads(result.stdout)['issues']))

    def test_converter_checks_reproducible_outputs(self):
        result = subprocess.run([sys.executable, str(PACKAGE / 'scripts/convert.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_refresh_rejects_tracked_symlinks(self):
        checkout = self.root / 'checkout'
        subprocess.run(['git', 'clone', '--shared', '--quiet', str(PACKAGE.parent), str(checkout)], check=True)
        shutil.copytree(PACKAGE, checkout / 'codex', dirs_exist_ok=True)
        outside = self.root / 'outside-note.txt'
        outside.write_text('A harmless outside fixture.')
        link = checkout / 'skills/seo/external-note.txt'
        link.symlink_to(outside)
        subprocess.run(['git', '-C', str(checkout), 'add', str(link)], check=True)
        result = subprocess.run([sys.executable, str(checkout / 'codex/scripts/convert.py'), '--write'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('regular file inside the checkout', result.stderr)
        self.assertFalse((checkout / 'codex/skills/seo/external-note.txt').exists())

    def test_unmapped_input_and_output_drift_fail_validation(self):
        source = self.root / 'checkout'
        source.mkdir()
        subprocess.run(['git', 'init', '-q', str(source)], check=True)
        upstream = source / 'skills/extra/SKILL.md'
        upstream.parent.mkdir(parents=True)
        upstream.write_text('---\nname: extra\ndescription: Example.\n---\n')
        subprocess.run(['git', '-C', str(source), 'add', 'skills'], check=True)
        package = source / 'codex'
        shutil.copytree(PACKAGE, package)
        result = subprocess.run([sys.executable, str(package / 'scripts/validate.py')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unmapped', result.stderr)

    def test_converter_rejects_output_path_escape(self):
        spec = importlib.util.spec_from_file_location('seo_convert', PACKAGE / 'scripts/convert.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(ValueError):
            module.generated_path('runtime/../../outside.txt')
        with self.assertRaises(ValueError):
            module.generated_path('runtime/../README.md')
        with self.assertRaises(ValueError):
            module.frontmatter('---\nname: ../../escape\ndescription: Example.\n---\n')

    def test_refresh_excludes_untracked_notes(self):
        checkout = self.root / 'checkout'
        subprocess.run(['git', 'clone', '--shared', '--quiet', str(PACKAGE.parent), str(checkout)], check=True)
        shutil.copytree(PACKAGE, checkout / 'codex', dirs_exist_ok=True)
        notes = checkout / 'skills/seo/private-notes.txt'
        notes.write_text('Local fixture notes must stay outside the package.')
        result = subprocess.run([sys.executable, str(checkout / 'codex/scripts/convert.py'), '--write'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((checkout / 'codex/skills/seo/private-notes.txt').exists())
        result = subprocess.run([sys.executable, str(checkout / 'codex/scripts/validate.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_copies_preserve_security_sources(self):
        mapping = json.loads((PACKAGE / 'docs/source-map.json').read_text())
        for name in ('url_safety.py', 'runtime.py', 'fetch_page.py', 'render_page.py'):
            target = PACKAGE / 'runtime/scripts' / name
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), mapping['upstream_files']['scripts/' + name])


if __name__ == '__main__':
    unittest.main()
