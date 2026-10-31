# Configure optional SEO services

Install the Codex skills first. Configure only the provider required for your task. Do not run the upstream extension installers. They write Claude configuration.

## Configure MCP providers

Use Codex MCP settings in the parent session. Review the sample in [mcp-config.toml](../templates/mcp-config.toml). Copy only the provider sections you need into your Codex configuration. Supply secrets through the named environment variables. Do not put keys in command arguments or tracked files.

The sample keeps the package versions selected by the upstream installers. It does not establish that a provider is connected. Restart the session, discover available tools, and verify their schemas before a live call. Provider calls can consume credits.

For DataForSEO, set `FIELD_CONFIG_PATH` to the absolute path of `runtime/extensions/dataforseo/field-config.json` in this package. Codex does not expand `${CODEX_SEO_ROOT}` inside TOML. The optional field configuration controls response size.

## Use direct API integrations

These workflows use bundled scripts through `scripts/codex-seo.py` after runtime setup.

| Workflow | Required environment or tool | Action |
| --- | --- | --- |
| Google | Use `run google_auth.py --check` to inspect the configured tier without showing credentials. | Follow [Google authentication](../skills/seo-google/references/auth-setup.md). Existing supported files remain under `~/.config/claude-seo/`. |
| Bing | Set `BING_WEBMASTER_API_KEY`. | Use `$seo-bing`. IndexNow also needs `INDEXNOW_KEY` and optionally `INDEXNOW_KEY_LOCATION`. Submit only when requested. |
| Matomo | Set `MATOMO_URL`, `MATOMO_API_TOKEN`, and optionally `MATOMO_SITE_ID`. | Use `run matomo_auth.py --check`, then `$seo-matomo`. |
| Unlighthouse | Install Node and `npx` when requested. | `$seo-unlighthouse` runs the pinned upstream CLI wrapper. |
| Banana direct generation | Set `GOOGLE_AI_API_KEY` and a verified `NANOBANANA_MODEL`. | The bundled `generate.py` and `edit.py` are available through `run --extension banana`. Generation requires user intent and cost approval. `batch.py` produces a plan. |

## Handle unavailable providers

Profound and SE Ranking ship procedures but no API client or MCP server. Connect a real provider tool or use user-supplied exports. Report live metrics as unavailable until evidence exists. Setting a key alone does not enable these workflows.

Ahrefs and SE Ranking have provider-specific units. The bundled DataForSEO cost helper estimates only endpoints in its own catalogue. It can log supplied actual costs. It does not provide an Ahrefs or SE Ranking estimate. Obtain current provider cost information before paid work.

The image audit agent only proposes images. It does not generate them. The DataForSEO agent uses MCP only. It must return unavailable when MCP is missing, even if a separate REST helper exists.
