# Codex SEO

Use SEO skills and specialist agents in Codex while retaining the original upstream project. All conversion files live in `codex/`. The original skills, agents, installers, and documentation remain unchanged.

The package contains 33 unique skills and 20 native agent procedures. This includes all 26 core skills and all nine extensions. Duplicate extension mirrors install once. Optional services need their own tools, credentials, and user authority.

## Install skills and agents

Keep this checkout at a stable path. The installer creates symlinks to it. Preview a project installation, then apply it.

```sh
python3 ~/Projects/codex-seo/codex/scripts/install.py --project /absolute/path/to/project
python3 ~/Projects/codex-seo/codex/scripts/install.py --project /absolute/path/to/project --apply
```

For user-wide discovery, use `--user` in place of `--project`. User skills go under `~/.agents/skills/`. Agents go under `$CODEX_HOME/agents/` or `~/.codex/agents/`. The installer refuses conflicting paths. It does not edit your project instructions or configuration.

Restart Codex after installing agent files. Use the name shown in the skill selector. Codex CLI 0.165 qualifies these names with `codex-seo:`. Invoke a skill in a prompt.

```text
$codex-seo:seo-audit https://example.com
$codex-seo:seo-schema Review the JSON-LD in this page.
$codex-seo:seo plan local-service
```

Check runtime readiness before execution.

```sh
python3 ~/Projects/codex-seo/codex/scripts/codex-seo.py doctor --json
```

When you want to install the Python dependencies and Chromium, run setup.

```sh
python3 ~/Projects/codex-seo/codex/scripts/codex-seo.py setup
```

Setup requires Python 3.11 through 3.14 and network access. The runtime uses its own environment under `~/.local/share/codex-seo/`. Read [CODEX.md](CODEX.md) for environment overrides and the shared legacy credential and cache paths.

To preview removal of links owned by this checkout, add `--uninstall` to the installation command. Add `--apply` to remove those links. User files and foreign links remain intact. The runtime environment and reports remain on disk.

## Use as a plugin

`codex/plugin.json` is a portable Agent Plugins manifest. Add this folder to a local marketplace with `source.path` pointing at `./codex`. A plugin bundles skills and runtime resources. Native agent files still need the installer or the documented full-procedure fallback.

Plugin directory publication and live third-party connections are separate from local installation. See the [official plugin packaging guide](https://developers.openai.com/plugins/build/plugins).

## Maintain the port

Read [the upstream refresh guide](docs/upstream.md). Run the local checks from the repository root.

```sh
python3 codex/scripts/validate.py
python3 -m unittest discover -s codex/tests -v
```

[The source audit](docs/audit.md) records the migration decisions and provider limits. [The source map](docs/source-map.json) records source and generated hashes. [Extension setup](docs/extensions.md) describes provider configuration.

The original MIT licence is retained at [LICENSE](LICENSE). FLOW prompt resources retain their upstream CC BY 4.0 credit and licence notices.
