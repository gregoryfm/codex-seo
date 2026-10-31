#!/usr/bin/env python3
"""Check independent source coverage, generated drift, skills, and native agents."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE.parent


def validate() -> list[str]:
    issues = []
    mapping = json.loads((PACKAGE / 'docs/source-map.json').read_text())
    ignored = subprocess.run(
        ['git', 'check-ignore', '--no-index', '--stdin', '-z'], cwd=SOURCE,
        input=''.join('codex/' + path + '\0' for path in mapping['generated_files']),
        capture_output=True, text=True, check=False,
    )
    if ignored.stdout:
        issues.append('Generated resources excluded by Git ignore rules: ' + ', '.join(ignored.stdout.rstrip('\0').split('\0')))
    files = subprocess.run(['git', 'ls-files', '-z'], cwd=SOURCE, check=True, capture_output=True).stdout.decode().split('\0')
    inventory = {p for p in files if p and not p.startswith('codex/')}
    if inventory != set(mapping['upstream_files']):
        issues.append('The independent upstream inventory differs from the recorded baseline.')
    for path in sorted(inventory):
        source = SOURCE / path
        if source.is_symlink() or not source.resolve().is_relative_to(SOURCE.resolve()):
            issues.append(f'Source must be a regular file inside the checkout: {path}')
            continue
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != mapping['upstream_files'].get(path):
            issues.append(f'Upstream source changed: {path}')
    covered = {entry['source'] for entry in mapping['resources']}
    if covered - inventory:
        issues.append('Mapped sources outside the tracked inventory: ' + ', '.join(sorted(covered - inventory)))
    required = {p for p in inventory if p.startswith(('skills/', 'agents/')) or re.match(r'extensions/[^/]+/(?:skills|agents)/', p)}
    if required - covered:
        issues.append('Unmapped skills, agents, or resources: ' + ', '.join(sorted(required - covered)))
    expected_skills = {Path(p).parent.name for p in inventory if p.endswith('/SKILL.md')}
    skills = sorted((PACKAGE / 'skills').glob('*/SKILL.md'))
    if {p.parent.name for p in skills} != expected_skills:
        issues.append('The unique skill inventory is incomplete or contains extra skills.')
    expected_agents = {Path(p).stem for p in required if re.search(r'(?:^|/)agents/[^/]+\.md$', p)}
    agents = sorted((PACKAGE / 'agents').glob('*.toml'))
    if {p.stem for p in agents} != expected_agents:
        issues.append('The unique agent inventory is incomplete or contains extra agents.')
    for path in skills:
        text = path.read_text()
        try:
            header, body = text[4:].split('\n---\n', 1)
            name = re.search(r'^name: (.+)$', header, re.M).group(1)
            description = json.loads(re.search(r'^description: (.+)$', header, re.M).group(1))
            if name != path.parent.name or not description or len(description) > 1024:
                issues.append(f'Invalid skill metadata: {path.relative_to(PACKAGE)}')
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
                issues.append(f'Invalid skill name: {name}')
            if any(key in header for key in ('maxTurns:', 'model:', 'tools:', 'user-invocable:', 'argument-hint:')):
                issues.append(f'Unsupported skill frontmatter: {name}')
            if '${CLAUDE_PLUGIN_ROOT}' in body or '${CLAUDE_SKILL_DIR}' in body or '~/.claude/' in body:
                issues.append(f'Unconverted host path: {name}')
        except (ValueError, AttributeError):
            issues.append(f'Invalid skill frontmatter: {path}')
    for path in PACKAGE.rglob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    for path in agents:
        role = tomllib.loads(path.read_text())
        if set(role) != {'name', 'description', 'developer_instructions'} or role['name'] != path.stem:
            issues.append(f'Invalid native agent: {path.name}')
    for path in [PACKAGE / 'README.md', PACKAGE / 'CODEX.md', *(PACKAGE / 'skills').rglob('*.md'), *(PACKAGE / 'docs').glob('*.md')]:
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            target = link.split('#')[0]
            if not target or re.match(r'(?:[a-z]+:|/|\$|<)', target):
                continue
            if target in ('url', 'SOUTH,WEST,NORTH,EAST'):
                continue
            if not (path.parent / target).exists():
                issues.append(f'Missing resource link: {path.relative_to(PACKAGE)} -> {target}')
    for name in ('setup_mcp.py', 'validate_setup.py'):
        if list((PACKAGE / 'runtime/extensions').rglob(name)):
            issues.append(f'Claude configuration helper must not ship: {name}')
    result = subprocess.run([sys.executable, str(PACKAGE / 'scripts/convert.py')], capture_output=True, text=True)
    if result.returncode:
        issues.append(result.stdout or result.stderr)
    return issues


def main() -> int:
    issues = validate()
    if issues:
        print('\n'.join(issues), file=sys.stderr)
        return 1
    print('PASS: upstream files retained; every skill and agent covered; generated resources current; native metadata valid.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
