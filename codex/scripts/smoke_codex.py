#!/usr/bin/env python3
"""Verify installed discovery with a real Codex app-server and no model calls."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading

PACKAGE = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    executable = shutil.which('codex')
    if not executable:
        print('Codex CLI is unavailable.', file=sys.stderr)
        return 77
    with tempfile.TemporaryDirectory(prefix='codex seo discovery ') as scratch:
        base = Path(scratch).resolve()
        project = base / 'project with spaces'
        package = project / 'plugins/codex-seo'
        shutil.copytree(PACKAGE, package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        env = {**os.environ, 'CODEX_HOME': str(base / 'codex home'), 'CODEX_SEO_DATA_DIR': str(base / 'runtime data')}
        (base / 'codex home').mkdir()
        installed = subprocess.run([sys.executable, str(package / 'scripts/install.py'), '--project', str(project), '--apply'], capture_output=True, text=True, env=env, check=True)
        links = json.loads(installed.stdout)['changes']
        marketplace = project / '.agents/plugins/marketplace.json'
        marketplace.parent.mkdir(parents=True, exist_ok=True)
        marketplace.write_text(json.dumps({'name': 'codex-seo-test', 'plugins': [{'name': 'codex-seo', 'source': {'source': 'local', 'path': './plugins/codex-seo'}, 'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}, 'category': 'Productivity'}]}))
        messages: queue.Queue = queue.Queue()
        with (base / 'stderr.log').open('w') as stderr:
            process = subprocess.Popen([executable, 'app-server', '--stdio'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True, env=env, cwd=project)

            def read_messages() -> None:
                for line in process.stdout:
                    messages.put(json.loads(line))
                messages.put({'error': 'app-server closed before replying'})

            threading.Thread(target=read_messages, daemon=True).start()

            def request(number: int, method: str, params: dict) -> dict:
                process.stdin.write(json.dumps({'id': number, 'method': method, 'params': params}) + '\n')
                process.stdin.flush()
                while True:
                    try:
                        reply = messages.get(timeout=30)
                    except queue.Empty:
                        raise RuntimeError('app-server timed out: ' + (base / 'stderr.log').read_text()) from None
                    if 'error' in reply and 'id' not in reply:
                        raise RuntimeError(str(reply['error']) + ': ' + (base / 'stderr.log').read_text())
                    if reply.get('id') == number:
                        if 'error' in reply:
                            raise RuntimeError(reply['error'])
                        return reply['result']

            try:
                initialized = request(1, 'initialize', {'clientInfo': {'name': 'codex-seo-smoke', 'version': '1.0.0'}, 'capabilities': {'experimentalApi': True}})
                discovered = request(2, 'skills/list', {'cwds': [str(project)], 'forceReload': True})
                data = discovered['data'][0]
                skills = [skill for skill in data['skills'] if Path(skill['path']).resolve().is_relative_to(package)]
                expected = {'codex-seo:' + skill.parent.name for skill in (package / 'skills').glob('*/SKILL.md')}
                actual = {skill['name'] for skill in skills}
                if actual != expected or data['errors']:
                    raise RuntimeError({'missing': sorted(expected - actual), 'extra': sorted(actual - expected), 'errors': data['errors']})
                plugins = request(3, 'plugin/list', {'cwds': [str(project)], 'forceRefetch': False, 'marketplaceKinds': ['local']})
                plugin_text = json.dumps(plugins)
                if 'codex-seo-test' not in plugin_text or 'codex-seo' not in plugin_text:
                    raise RuntimeError('The local plugin marketplace was not discovered.')
                receipt = {'client': initialized['userAgent'], 'skills': sorted(actual), 'skill_count': len(actual), 'skill_errors': data['errors'], 'linked_agents': len([link for link in links if link['destination'].endswith('.toml')]), 'plugin_marketplace_discovered': True, 'package_copy_outside_upstream_checkout': True, 'model_calls': 0}
                print(json.dumps(receipt, indent=2))
                if args.receipt:
                    args.receipt.parent.mkdir(parents=True, exist_ok=True)
                    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
