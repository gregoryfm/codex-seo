#!/usr/bin/env python3
"""Generate the Codex alternative from untouched upstream resources."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE.parent
RUNTIME = 'python3 "${CODEX_SEO_ROOT}/scripts/codex-seo.py"'
CONTRACT = "Read [the Codex runtime contract](../../CODEX.md) before this workflow. Resolve CODEX_SEO_ROOT from this skill's resolved file path, two directories above its folder. Use that absolute package path in each shell command. Read relative resources from this skill folder, then the shared skills/seo folder when needed.\n\n"


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith('---\n'):
        raise ValueError('missing frontmatter')
    header, body = text[4:].split('\n---\n', 1)
    fields: dict[str, str] = {}
    current = ''
    for line in header.splitlines():
        match = re.match(r'^([\w-]+):\s*(.*)$', line)
        if match:
            current, value = match.groups()
            if value in ('>', '|'):
                value = ''
            fields[current] = value
        elif current and line.startswith('  '):
            fields[current] += ' ' + line.strip()
    for key in ('name', 'description'):
        if key not in fields:
            raise ValueError(f'missing {key}')
        value = fields[key].strip()
        if value.startswith('"') and value.endswith('"'):
            # Several upstream descriptions have over-escaped embedded quotes.
            value = value[1:-1].replace('\\\\"', '"').replace('\\"', '"')
        fields[key] = value
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', fields['name']) or len(fields['name']) > 64:
        raise ValueError(f'Invalid component name: {fields["name"]}')
    return fields, body.lstrip('\n')


def adapt(text: str) -> str:
    text = text.replace('"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo"', RUNTIME)
    text = text.replace('${CLAUDE_PLUGIN_ROOT}', '${CODEX_SEO_ROOT}')
    text = text.replace('${CLAUDE_SKILL_DIR}/', '')
    text = text.replace('${CLAUDE_SKILL_DIR}', 'the resolved current skill folder')
    text = text.replace('/seo ', '$seo ').replace('`/seo`', '`$seo`')
    text = re.sub(r'parse_html\.py <(?:URL|url)>', 'parse_html.py --url <url>', text)
    text = text.replace('`/seo-', '`$seo-')
    text = text.replace('Claude Code', 'Codex').replace('Claude SEO', 'Codex SEO')
    text = re.sub(r'agents/(seo-[a-z-]+)\.md', r'agents/\1.toml', text)
    text = text.replace('extensions/matomo/docs/MATOMO-SETUP.md', 'docs/extensions.md').replace('SECURITY.md', 'CODEX.md')
    text = text.replace('claude-seo uses a', 'Codex SEO uses a')
    lines = []
    for line in text.splitlines(keepends=True):
        if re.search(r'(?:\./)?extensions/[a-z-]+/install\.(?:sh|ps1)', line):
            if line.lstrip().startswith('|'):
                line = re.sub(r'(?:\./)?extensions/[a-z-]+/install\.(?:sh|ps1)', 'docs/extensions.md', line)
            elif line.lstrip().startswith(('via ', '(Windows)', '(Unix)')):
                line = 'Read `${CODEX_SEO_ROOT}/docs/extensions.md` for Codex setup.\n'
            else:
                line = 'Read `${CODEX_SEO_ROOT}/docs/extensions.md` for Codex setup.\n'
        if '~/.claude/settings.json' in line or '~/.claude.json' in line:
            line = 'Use the required environment variables or configured Codex MCP tools. Read `${CODEX_SEO_ROOT}/docs/extensions.md`. Never read Claude credential stores.\n'
        lines.append(line)
    text = ''.join(lines)
    text = re.sub(r'```(?:bash|sh)\n(?:#[^\n]*\n)*Read `\$\{CODEX_SEO_ROOT\}/docs/extensions.md` for Codex setup\.\n```', 'Read `${CODEX_SEO_ROOT}/docs/extensions.md` for Codex setup.', text)
    text = text.replace('pip install playwright && playwright install chromium', RUNTIME + ' setup')
    text = text.replace('~/.claude/skills/blog/SKILL.md', 'the installed Codex skill catalogue entry for blog-write')
    text = text.replace('~/.claude/plugins/cache/*/claude-blog/*/skills/blog/SKILL.md', 'the resolved Codex blog-write skill path')
    text = text.replace('run --extension banana setup_mcp.py --key YOUR_KEY', 'doctor --json')
    text = text.replace('pip install google-ads', RUNTIME + ' setup')
    text = text.replace('run --extension banana validate_setup.py', 'doctor --json')
    return text


def generated_path(relative: str) -> Path:
    path = PACKAGE / relative
    parts = Path(relative).parts
    allowed = parts and parts[0] in ('skills', 'agents', 'runtime', 'assets', 'LICENSE', '.codex-plugin', 'plugin.json')
    allowed = allowed or relative == 'docs/source-map.json'
    if not allowed or '..' in parts or not path.resolve().is_relative_to(PACKAGE.resolve()):
        raise ValueError(f'Unsafe generated output path: {relative}')
    return path


def skill_text(path: Path) -> tuple[str, str]:
    fields, body = frontmatter(path.read_text())
    name = fields['name']
    if name == 'seo':
        start = body.index('**Invocation:**')
        end = body.index('Comprehensive SEO analysis', start)
        body = body[:start] + '**Invocation:** Use `$seo <command> <arguments>` or invoke a specific `$seo-*` skill. These are prompt instructions, not shell commands.\n\n' + body[end:]
        start = body.index('### Optional Extensions')
        end = body.index('## Subagents', start)
        body = body[:start] + '### Optional extensions\n\nAll nine extension procedures are bundled. Read [Codex extension setup](../../docs/extensions.md) before configuring a provider. Tool availability and credentials determine whether a procedure can run.\n\n' + body[end:]
    if name in ('seo-profound', 'seo-seranking'):
        body = 'Live execution requires an actual connected provider tool or a supplied export. No API client is bundled. An environment key alone is insufficient. Report unavailable data honestly.\n\n' + body
    if name == 'seo-ahrefs':
        body = body.replace('Estimate cost with `\"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo\" run dataforseo_costs.py` (the cost-tracker module is generic and supports Ahrefs unit accounting).', 'Obtain a current Ahrefs unit estimate. The DataForSEO helper does not estimate Ahrefs units.')
    if name == 'seo-agentic':
        start = body.index('## Refresh mode')
        end = body.index('## Security', start)
        body = body[:start] + '## Refresh mode\n\nVerify the dated claims against primary sources and return a proposed update with evidence. Do not edit the installed package. Read `${CODEX_SEO_ROOT}/docs/upstream.md` for source maintenance.\n\n' + body[end:]
    if name == 'seo-dataforseo':
        body = body.replace('Report that DataForSEO extension is not installed or MCP server is unreachable.', 'Report that DataForSEO MCP tools are unavailable in this session. Their absence does not prove the extension is uninstalled.')
        body = body.replace('inform the user the extension is not\ninstalled and provide install instructions.', 'report that the tools are unavailable in this session and read the Codex extension setup guide.')
    if name == 'seo-flow':
        start = body.index('### On `/seo flow sync`')
        end = body.index('---', start)
        body = body[:start] + '### On `/seo flow sync`\n\nRead `${CODEX_SEO_ROOT}/docs/upstream.md` for the maintainer refresh procedure. No installed resources are changed. Do not report a completed sync.\n\n' + body[end:]
        body = body.replace('Run `/seo flow sync` to pull the latest prompts from the FLOW repo.', 'Read `${CODEX_SEO_ROOT}/docs/upstream.md` to refresh source resources.')
        body = body.replace('Run: `/seo flow sync`', 'Read `${CODEX_SEO_ROOT}/docs/upstream.md`')
        body = '\n'.join(line for line in body.splitlines() if not line.startswith('| `sync_flow.py`')) + '\n'
    description = fields['description'].replace('/seo ', '$seo ')
    header = f'---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n'
    for key in ('license',):
        if key in fields:
            header += f'{key}: {fields[key]}\n'
    if 'metadata' in fields:
        raw_header = path.read_text()[4:].split('\n---\n', 1)[0]
        match = re.search(r'(?m)^metadata:\n((?:[ \t]+[^\n]*\n?)+)', raw_header)
        if match:
            header += 'metadata:\n' + match.group(1).rstrip() + '\n'
    return name, header + '---\n\n' + CONTRACT + adapt(body)


def source_files() -> list[Path]:
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=SOURCE, check=True, capture_output=True)
    files = sorted(SOURCE / p for p in result.stdout.decode().split('\0') if p and not p.startswith('codex/'))
    for path in files:
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(SOURCE.resolve()):
            raise ValueError(f'Source must be a regular file inside the checkout: {path.relative_to(SOURCE)}')
    return files


def build() -> tuple[dict[str, bytes], dict]:
    outputs: dict[str, bytes] = {}
    mappings = []
    files = source_files()

    def add(source: Path, target: str, content: bytes | None = None, *, mirror: bool = False) -> None:
        value = source.read_bytes() if content is None else content
        if target in outputs and outputs[target] != value and not mirror:
            raise ValueError(f'conflicting mirrored resource: {source} -> {target}')
        outputs[target] = value
        mappings.append({'source': source.relative_to(SOURCE).as_posix(), 'target': target,
                         'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})

    skills = [path for path in files if re.fullmatch(r'skills/[^/]+/SKILL\.md', path.relative_to(SOURCE).as_posix())]
    skills += [path for path in files if re.fullmatch(r'extensions/[^/]+/skills/[^/]+/SKILL\.md', path.relative_to(SOURCE).as_posix())]
    for skill in skills:
        name, content = skill_text(skill)
        add(skill, f'skills/{name}/SKILL.md', content.encode(), mirror=name == 'seo-image-gen')
        for resource in files:
            if not resource.is_relative_to(skill.parent) or resource == skill:
                continue
            relative = resource.relative_to(skill.parent)
            content_bytes = resource.read_bytes()
            if resource.suffix == '.md' and 'prompts' not in relative.parts:
                content_bytes = adapt(content_bytes.decode()).encode()
            add(resource, f'skills/{name}/{relative.as_posix()}', content_bytes)

    agent_paths = [path for path in files if re.fullmatch(r'agents/[^/]+\.md', path.relative_to(SOURCE).as_posix())]
    agent_paths += [path for path in files if re.fullmatch(r'extensions/[^/]+/agents/[^/]+\.md', path.relative_to(SOURCE).as_posix())]
    for agent in agent_paths:
        fields, body = frontmatter(agent.read_text())
        name = fields['name']
        contract = ('Read the CODEX.md at the absolute CODEX_SEO_ROOT supplied by the parent. '
                    'If that package path is missing, ask the parent for it before running tools. '
                    'Resolve all skill resources below that package. '
                    'Use only tools available in this session. The upstream tool list is an instruction boundary, not a separate sandbox. '
                    'If writes are permitted, write only the assigned findings path. Otherwise return findings to the parent for persistence. Return partial findings before the host budget ends.\n\n')
        restrictions = 'Upstream permitted operations: ' + fields.get('tools', '').split('#')[0].strip() + '.\n'
        instructions = contract + restrictions + '\n' + adapt(body)
        if 'Bash' not in fields.get('tools', ''):
            instructions = instructions.replace('Bash is not available to this agent, do not attempt shell execution', 'Use shell-backed file reads and searches only when the host has no separate Read, Glob, or Grep tool. Do not run programs, installs, or API commands')
            instructions += '\nOn Codex, shell-backed file reads and searches implement the permitted Read, Glob, and Grep operations. Other shell execution remains forbidden.\n'
        if name == 'seo-visual':
            instructions = instructions.replace('Before capturing screenshots, ensure Playwright and Chromium are installed:', 'Check runtime readiness before screenshots. Run setup only when the user requests dependency setup or repair:')
        content = '\n'.join([f'name = {json.dumps(name)}', f'description = {json.dumps(fields["description"])}', f'developer_instructions = {json.dumps(instructions, ensure_ascii=False)}', ''])
        add(agent, f'agents/{name}.toml', content.encode())

    runtime_ast = ast.parse((SOURCE / 'scripts/runtime.py').read_text())
    declaration = next(node.value for node in runtime_ast.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == 'ALLOWED_CORE_SCRIPTS'
                               for target in node.targets))
    runtime_scripts = ast.literal_eval(declaration.args[0]) | {'runtime.py'}
    for path in files:
        relative = path.relative_to(SOURCE).as_posix()
        if (relative.startswith('scripts/') and path.name in runtime_scripts) or relative.startswith(('schema/', 'data/')) or relative == 'requirements.txt':
            add(path, f'runtime/{relative}')
        elif relative == 'LICENSE':
            add(path, relative)
        elif relative == 'hooks/validate-schema.py':
            content = path.read_text()
            content = content.replace('    if schema_type in deprecated:', '    schema_types = schema_type if isinstance(schema_type, list) else [schema_type]\n    if not schema_types or any(not isinstance(item, str) for item in schema_types):\n        errors.append(f"{prefix}: @type must be a string or a non-empty list of strings")\n        schema_types = []\n    for schema_type in schema_types:\n        if schema_type in deprecated:')
            content = '\n'.join(
                '    ' + line if line.startswith('        errors.append')
                and any(token in line for token in ('{deprecated[schema_type]}', '{restricted[schema_type]}'))
                else line for line in content.splitlines()
            ) + '\n'
            content = content.replace('    if schema_type in restricted:', '    for schema_type in schema_types:\n        if schema_type in restricted:')
            add(path, f'runtime/{relative}', content.encode())
        elif relative == 'extensions/dataforseo/field-config.json':
            add(path, f'runtime/{relative}')
        elif relative == 'assets/framework.svg':
            add(path, relative)
        elif re.match(r'extensions/[^/]+/scripts/[^/]+\.py$', relative) and path.name not in ('setup_mcp.py', 'validate_setup.py'):
            add(path, f'runtime/{relative}')
    manifest = json.loads((SOURCE / '.claude-plugin/plugin.json').read_text())
    outputs['runtime/runtime-plugin.json'] = (json.dumps({'version': manifest['version']}, indent=2) + '\n').encode()
    plugin = {'$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
              'name': 'codex-seo', 'version': manifest['version'],
              'description': 'SEO audits, content analysis, structured data, local search, and optional provider workflows for Codex.',
              'license': 'MIT'}
    add(SOURCE / '.claude-plugin/plugin.json', 'plugin.json', (json.dumps(plugin, indent=2) + '\n').encode())
    plugin.pop('$schema')
    plugin['skills'] = './skills/'
    add(SOURCE / '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', (json.dumps(plugin, indent=2) + '\n').encode())
    revision = subprocess.run(['git', 'log', '-1', '--format=%H', '--', '.', ':!codex'], cwd=SOURCE, check=True, capture_output=True, text=True).stdout.strip()
    upstream = {p.relative_to(SOURCE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    source_map = {'schema_version': 1, 'upstream_url': 'https://github.com/AgriciDaniel/claude-seo', 'upstream_revision': revision,
                  'upstream_version': manifest['version'], 'upstream_files': upstream, 'resources': mappings,
                  'generated_files': {p: hashlib.sha256(data).hexdigest() for p, data in sorted(outputs.items())}}
    outputs['docs/source-map.json'] = (json.dumps(source_map, indent=2, sort_keys=True) + '\n').encode()
    return outputs, source_map


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='refresh only generated Codex resources')
    args = parser.parse_args()
    outputs, source_map = build()
    stale = [path for path, value in outputs.items() if not (PACKAGE / path).is_file() or (PACKAGE / path).read_bytes() != value]
    previous = PACKAGE / 'docs/source-map.json'
    old_paths = set(json.loads(previous.read_text()).get('generated_files', {})) if previous.exists() else set()
    removed = old_paths - set(outputs)
    if args.write:
        for path in removed:
            generated_path(path).unlink(missing_ok=True)
        for path, value in outputs.items():
            target = generated_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
    elif stale or removed:
        print('Codex resources need regeneration:')
        for path in sorted(set(stale) | removed):
            print(path)
        return 1
    print(f'{len(source_map["resources"])} source resources; {len(list((PACKAGE / "skills").glob("*/SKILL.md")))} skills; {len(list((PACKAGE / "agents").glob("*.toml")))} agents; generated files {"updated" if args.write else "current"}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
