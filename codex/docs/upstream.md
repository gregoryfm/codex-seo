# Refresh the Codex alternative

Run these commands from the repository root. Keep hand-written Codex changes inside `codex/`. Treat `codex/skills/`, `codex/agents/`, and `codex/runtime/` as generated files.

1. Fetch the upstream repository.

```sh
git remote add upstream https://github.com/AgriciDaniel/claude-seo.git
git fetch upstream
```

Skip `remote add` when the remote already exists. Review the upstream diff before merging.

2. Merge the reviewed upstream revision.

```sh
git merge upstream/main
```

All port changes live in the added `codex/` directory. Existing upstream files have no port edits to reconcile. Conflicts remain possible if upstream later introduces the same directory.

3. Review changed skills, agents, provider installers, and runtime contracts. Update `codex/scripts/convert.py` when new host-specific syntax appears.

4. Regenerate and validate the Codex files.

```sh
python3 codex/scripts/convert.py --write
python3 codex/scripts/validate.py
python3 -m unittest discover -s codex/tests -v
```

5. Inspect the generated diff and commit it with the upstream update.

The converter records source revision, file hashes, duplicate mirrors, and output hashes in `docs/source-map.json`. It discovers inputs independently from that map. Default invocation checks for drift and writes nothing. `--write` updates generated outputs and removes outputs retired by the previous generated map.

The Banana extension skill is the canonical `seo-image-gen` procedure. It includes the local generation helpers absent from the core mirror. Both source files remain recorded. The DataForSEO and duplicate agent mirrors produce one installed procedure per name.

For FLOW updates, use the upstream project's reviewed source update procedure, then regenerate the Codex package. `sync_flow.py` is disabled in installed packages. For `seo-agentic refresh`, return dated findings to the user. A maintainer can apply them to the upstream source and regenerate. Do not edit generated resources or the plugin cache during an audit.

After regenerating agent procedures, rerun `scripts/install.py` with `--apply` for each installed scope to refresh unchanged managed copies. Preview first. The installer records copied file hashes and preserves agent files edited since the last install.
