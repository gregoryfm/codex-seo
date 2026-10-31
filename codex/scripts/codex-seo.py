#!/usr/bin/env python3
"""Run the bundled SEO tools with a separate Codex runtime."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parents[1]
RUNTIME = PACKAGE / 'runtime'
MAINTAINER_SCRIPTS = {'sync_flow.py', 'consistency_check.py', 'portability_check.py'}
CLAUDE_SETUP_SCRIPTS = {'setup_mcp.py', 'validate_setup.py'}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def interpreter() -> str:
    configured = os.environ.get('CODEX_SEO_PYTHON')
    candidates = [configured] if configured else [sys.executable, *[shutil.which(f'python3.{minor}') for minor in range(14, 10, -1)]]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            result = subprocess.run([candidate, '-c', 'import sys; print(3, 11 <= sys.version_info.minor <= 14 and sys.version_info.major == 3)'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip() == '3 True':
                return candidate
        except (OSError, subprocess.TimeoutExpired):
            continue
    raise ValueError('Python 3.11 through 3.14 is required. Set CODEX_SEO_PYTHON to a supported executable.')


def validate_schema(path: str) -> int:
    target = Path(path)
    if target.stat().st_size > 10 * 1024 * 1024:
        raise ValueError('Schema input exceeds 10 MiB.')
    content = target.read_text(encoding='utf-8')
    if target.suffix.lower() in ('.json', '.jsonld'):
        value = json.loads(content)
        content = '<script type="application/ld+json">' + json.dumps(value).replace('<', '\\u003c') + '</script>'
    elif target.suffix.lower() not in ('.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte', '.php', '.ejs'):
        raise ValueError('Provide a JSON-LD or HTML-like file.')
    module = load_module('seo_schema_validation', RUNTIME / 'hooks/validate-schema.py')
    issues = module.validate_jsonld(content, str(target))
    print(json.dumps({'valid': not issues, 'issues': issues}, indent=2))
    return 2 if issues else 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        if args and args[0] == 'validate-schema':
            if len(args) != 2:
                raise ValueError('Usage: codex-seo.py validate-schema FILE')
            return validate_schema(args[1])
        runtime = load_module('seo_runtime', RUNTIME / 'scripts/runtime.py')
        parser = runtime.build_parser()
        parser.prog = 'codex-seo.py'
        parser.description = 'Codex SEO managed Python runtime'
        parser.epilog = 'Also available: validate-schema FILE. This does not require runtime setup.'
        parsed = parser.parse_args(args)
        if parsed.command == 'run':
            if parsed.script in MAINTAINER_SCRIPTS:
                raise ValueError('This source-maintenance command is unavailable in installed packages. Read docs/upstream.md.')
            if parsed.script in CLAUDE_SETUP_SCRIPTS:
                raise ValueError('Use Codex MCP configuration. Read docs/extensions.md.')
        env = os.environ.copy()
        data = Path(env.get('CODEX_SEO_DATA_DIR', '~/.local/share/codex-seo')).expanduser().resolve()
        if data == Path(data.anchor) or data == Path.home().resolve():
            raise ValueError('CODEX_SEO_DATA_DIR must be a dedicated subdirectory.')
        env['CLAUDE_PLUGIN_ROOT'] = str(RUNTIME)
        env.pop('CLAUDE_PLUGIN_DATA', None)
        env['CLAUDE_SEO_DATA_DIR'] = str(data)
        env['CLAUDE_SEO_CONFIG_DIR'] = str(data / 'costs')
        if env.get('CODEX_SEO_LOCAL_TARGETS'):
            env['CLAUDE_SEO_LOCAL_TARGETS'] = env['CODEX_SEO_LOCAL_TARGETS']
        return subprocess.run([interpreter(), str(RUNTIME / 'scripts/runtime.py'), *args], env=env).returncode
    except (OSError, ValueError, TypeError, subprocess.SubprocessError) as error:
        print(f'Codex SEO: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
