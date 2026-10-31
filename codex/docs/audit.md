# Codex conversion audit

The baseline is upstream version 2.5.0 at `6be93f45064ffbadced572b5d5c95f55fd263af0`. The source map records the precise files and hashes. The conversion adds a separate `codex/` package and preserves every pre-existing tracked file.

## Architecture

The source routes 26 core skills through `seo`, delegates to 19 specialist procedures, and exposes nine optional extensions. Two extension skills and two agent procedures mirror core names. Matomo contributes an additional agent. The installed result has 33 unique skills and 20 agent procedures.

The generated package contains skill resources, native TOML agents, Python execution scripts, bounded requirements, data, schema templates, provider helpers, and licence notices. The converter reads only tracked regular files inside the checkout. It rejects source symlinks. The converter owns generated files. The installer, adapter, documentation, and tests are maintained inside `codex/`.

A shared wrapper pointing at `../scripts` was considered. It would require the full upstream checkout at runtime. The selected self-contained copy preserves script-relative imports and supports a plugin cache or a separate copied package.

The domain model is a source inventory with source path, target path, source hash, and generated output hash. This follows Model the Domain. Build the Lever led to the repeatable converter. Laziness Protocol kept runtime execution scripts unchanged. Prove It Works led to an independent inventory check and real Codex discovery tests.

## Host adaptations

- Skill frontmatter keeps supported discovery fields and source metadata. Claude invocation and argument fields are removed.
- The native agent files inherit the selected Codex model. No equivalence between `sonnet`, `opus`, and a Codex model is claimed.
- Codex host budgets replace the unsupported hard `maxTurns` setting. Partial-finding persistence remains part of agent instructions.
- Native tool names are resolved through the session catalogue. Read, Glob, and Grep can use shell-backed reads when no separate file tool exists. This does not permit other shell commands in roles that exclude Bash.
- Each entrypoint resolves its package path and reads CODEX.md. Relative resources are retained. Runtime commands use the Codex adapter.
- The visual agent uses managed setup. No direct global pip install is required.
- Upstream extension installers and Banana's Claude configuration helpers are excluded from Codex setup.
- FLOW sync and agentic reference refresh return source-maintenance instructions. Audits do not modify generated resources or upstream files.
- Structured data uses an explicit validator instead of an automatic hook. The Codex adapter supports JSON files and neutral JSON results. The copied validator adapts multi-type JSON-LD without changing the original hook.
- The Banana extension is canonical where its core mirror differs. It includes local generation and cost-tracking helpers. Both originals remain in the source map.

## Verification boundaries

The local unit suite tests installer conflicts, repeat runs, uninstall ownership, dispatch restrictions, missing-runtime behaviour, schema output, source coverage, and reproducible conversion. `scripts/smoke_codex.py` copies the package outside the source checkout, installs it in a temporary project, and asks the real Codex app-server to discover skills and the local plugin marketplace. It makes no model calls.

The independent behavioural pass exercises schema placeholders, a local FLOW draft, and missing DataForSEO and Profound tools. It verifies resource resolution and unavailable-result behaviour. It does not prove every SEO judgment or every provider operation.

Paid services, authenticated APIs, browser rendering, provider installation, and actual native-role execution have their own verification gates. See `verification.json` for this run's observed results. Hosted CI and marketplace publication are separate from local checks.

A cross-model design and trail review was unavailable because distinct model families were not configured. The local source audit, correctness review, and behavioural checks do not replace that coverage.

## Core skills inventory

`Adapt` means the SEO procedure transfers but needs host syntax, runtime-root, or resource changes. `Conditional` means an external service, credentials, browser, or additional skill is essential for the complete workflow. Every skill remains subject to the shared requirements above.

| Skill | Status | Specific work or condition |
|---|---|---|
| seo | Adapt | Replace runtime preamble, slash-command entrypoints, installer guidance, and role dispatch. Keep managed setup explicit. Preserve capability-conditioned specialists and partial-result reporting. Keep human upstream credit and licence notices. |
| seo-agentic | Adapt | Preserve authorization for user-agent WAF testing, Lighthouse fraction versus heuristic distinction, and draft-only fix output. Refresh mode must update the Codex copy and matching runtime constant without modifying preserved upstream sources. |
| seo-audit | Adapt | Preserve 500-page crawl bound, robots rules, separate specialist outputs, report envelope, and conditional integrations. Replace `maxTurns` error wording with actual host budget handling. |
| seo-backlinks | Adapt | Preserve 4-of-7 data sufficiency and mandatory `validate_backlink_report.py` gate. Common-Crawl-only mode emits `Not Assessed`. Paid and credentialed sources are optional. Replace upstream installer advice. |
| seo-cluster | Adapt | Preserve reference methodology, plan JSON, map template, script-block escaping, and resume/link contracts. Replace `~/.claude` skill/cache probes with Codex catalogue discovery. `blog-write` is optional. Without a compatible installed skill, generate briefs. |
| seo-competitor-pages | Adapt | Natural language workflow transfers. Preserve public-source verification, dated pricing, affiliation disclosure, and local schema resource access. |
| seo-content | Adapt | Replace runtime paths in checks and shared reference links. Preserve deterministic draft cleanup, user-owned draft restriction, heuristic score labels, and source freshness checks. |
| seo-content-brief | Adapt | Preserve local excluded-domain, template, and keyword references. Live SERP and fetched site data are required for evidence-backed competitor claims. |
| seo-dataforseo | Conditional | Requires actual connected DataForSEO MCP tools. Replace all shell installers and runtime paths. Preserve per-call cost checks and unavailable-tool handling. No invented Images SERP tool. |
| seo-drift | Adapt | SQLite schema and baseline/compare/history flow transfer. Preserve legacy cache path if unchanged in scripts. Baseline and comparison commands intentionally write local state. Do not conflate running once with scheduled monitoring. |
| seo-ecommerce | Adapt | Static analysis transfers. Merchant REST and organic MCP are distinct paths. Preserve cost ledger checks and Product schema validation. Endpoint probes and paid calls remain scoped. |
| seo-flow | Adapt | Copy all prompts, stage index, framework, bibliography, and CC BY 4.0 credit. Replace sync command with a Codex-specific refresh workflow that cannot mutate original source paths. Keep selective optimize loading. |
| seo-geo | Adapt | Preserve crawler names and separate training/search/user-triggered meanings. Retain evidence status and date checks. Do not invent measured platform scores when premium tools are unavailable. |
| seo-google | Conditional | Requires Google config tier for authenticated data. Retain safe `google_auth.py --check`, environment/config contracts, totals_complete gate, report PASS gate, and explicit Indexing API submission intent. Resolve managed dependency setup instead of raw pip instructions in a reference. |
| seo-hreflang | Adapt | Transfer local format, cultural profile, content parity, and translation-QA references. Preserve output generation and web-fetch trust boundaries. |
| seo-image-gen | Conditional | Requires actual nanobanana MCP image tools for preserved provider behaviour. Audit agent is separate and never generates. Do not silently substitute an OpenAI provider as parity. Replace installer advice. MCP references currently mention direct API fallback, so the Codex contract must choose and state whether it remains supported. |
| seo-images | Adapt | Preserve image CLI capability checks, metadata/output distinction, and source-type confirmation for metadata writes. Tool-install snippets need host/platform-appropriate guidance and do not grant automatic package installation. |
| seo-local | Adapt | Preserve shared local references and business-type-conditioned checks. Paid maps visibility is separate from website evidence. Keep unknown fields and multi-location gates. |
| seo-maps | Conditional | Free tier needs external Overpass/Nominatim and optionally Geoapify. Premium tiers require connected DataForSEO/Google Maps. Preserve explicit geo-grid cost confirmation and unavailable fields. |
| seo-page | Adapt | Preserve single-page scope, metadata comparison command, and unknown CWV limitations. Optional DataForSEO enrichment remains conditional. |
| seo-plan | Adapt | Copy all six industry templates. Preserve current-site versus new-site mode and evidence-bound competitor estimates. A planning task does not authorise outreach or publication. |
| seo-programmatic | Adapt | Preserve scale/uniqueness gates and metadata set validation. Local planning and report generation transfer. Publication remains a distinct action. |
| seo-schema | Adapt | Copy schema templates and deprecated-type reference. Preserve truthful markup and pre-delivery validation. Relative `schema/templates.json` means package root, not current workspace. |
| seo-sitemap | Adapt | Preserve sitemap discovery helper and its found/failures semantics. Copy industry templates through sibling skill. Output XML generation is local. |
| seo-sxo | Adapt | Preserve taxonomy, user story, persona, and wireframe references. Keep separate SXO score. Search results must be observed; unavailable data is a limitation. |
| seo-technical | Adapt | Preserve SSRF allowlist contract, scope-limited CVE inspection, and not-measured status. Replace command syntax and link shared runtime/resources. Private hosts remain explicitly named by the operator. |

## Agent inventory

Every role needs native Codex configuration or full-procedure fallback. Original models are provenance, not supported target model names. Every listed role includes its own untrusted-content rule. Incremental persistence must survive the port.

| Role | Original model | Original maxTurns | Specific boundary or output |
|---|---|---:|---|
| seo-agentic | sonnet | 35 | No WAF user-agent matrix without authority. Writes findings/agentic.md. |
| seo-backlinks | sonnet | 40 | Source sufficiency and mandatory report validator. Writes findings/backlinks.md. |
| seo-cluster | opus | 40 | Search/read/write tools but no Bash in original tool list. Keep cluster-plan.json and findings/cluster.md. |
| seo-content | opus | 45 | Main-content extracted_text, not full page chrome. Writes findings/content.md. |
| seo-dataforseo | sonnet | 35 | MCP only. No credential-store inspection or raw HTTP fallback. Writes findings/dataforseo.md. |
| seo-drift | opus | 30 | Use SSRF-safe scripts only. No raw curl. Writes findings/drift.md. |
| seo-ecommerce | sonnet | 35 | Merchant cost checks. Writes findings/ecommerce.md. |
| seo-flow | sonnet | 15 | Explicit no-Bash role. At most five selected prompts. Required CC BY 4.0 credit. No findings persistence contract exists in source. |
| seo-geo | opus | 35 | Preserve crawler purpose separation. Writes findings/geo.md. |
| seo-google | sonnet | 35 | Preserve config tier, complete totals, report review PASS, and redacted errors. Writes findings/google.md. |
| seo-image-gen | sonnet | 15 | Audit-only. No generation. Original tools omit Write despite generation-plan output. Parent can persist the returned plan. No explicit incremental findings contract exists. |
| seo-local | sonnet | 32 | On-page local evidence. Writes findings/local.md. |
| seo-maps | sonnet | 40 | Free/premium tier separation and provider costs. Writes findings/maps.md. |
| seo-performance | sonnet | 35 | Real field data separate from lab data. Writes findings/performance.md. |
| seo-schema | sonnet | 35 | Rendered JSON-LD artifacts and full graph. Writes findings/schema.md. |
| seo-sitemap | sonnet | 30 | Validated discoveries and quality gates. Writes findings/sitemap.md. |
| seo-sxo | opus | 35 | Separate SXO score and SERP-backed persona evidence. Writes findings/sxo.md. |
| seo-technical | sonnet | 45 | Source versus measured CWV distinction. Writes findings/technical.md. |
| seo-visual | sonnet | 35 | Managed screenshot commands. Replace conflicting global `pip install playwright && playwright install chromium` prerequisite with explicit managed runtime setup. Writes findings/visual.md and screenshots. |


## Extension inventory

| Extension | Source skill | Codex adaptation | Conditional requirements |
| --- | --- | --- | --- |
| Ahrefs | `extensions/ahrefs/skills/seo-ahrefs/SKILL.md` | Replace installer and Claude config references with Codex stdio MCP setup. | `npx --yes --package=@ahrefs/mcp@0.0.11 mcp`; `AHREFS_API_TOKEN`; metered account. |
| Banana | `extensions/banana/skills/seo-image-gen/SKILL.md` | Translate skill and plugin paths, MCP setup, and audit-only agent. Do not reuse `setup_mcp.py` or `validate_setup.py` unchanged. | `npx -y @ycse/nanobanana-mcp@1.1.1`; `GOOGLE_AI_API_KEY`; optional `NANOBANANA_MODEL`; generation costs money. |
| Bing Webmaster | `extensions/bing-webmaster/skills/seo-bing/SKILL.md` | Use existing `bing_webmaster.py` and `indexnow_submit.py` via Codex launcher. Replace settings.json setup with process environment. | `BING_WEBMASTER_API_KEY`; IndexNow optionally requires `INDEXNOW_KEY` and `INDEXNOW_KEY_LOCATION`. Submit and submit-batch send URLs externally. |
| DataForSEO | `extensions/dataforseo/skills/seo-dataforseo/SKILL.md` | Translate paths and MCP setup, preserve cost approvals and MCP-only agent boundary. Core mirror already exists. | `npx -y dataforseo-mcp-server@2.8.10`; `DATAFORSEO_USERNAME`, `DATAFORSEO_PASSWORD`, `ENABLED_MODULES`, `FIELD_CONFIG_PATH`; every API call is metered. |
| Firecrawl | `extensions/firecrawl/skills/seo-firecrawl/SKILL.md` | Replace installer and WebFetch aliases with available Codex tools and Codex stdio MCP setup. | `npx -y firecrawl-mcp@3.11.0`; `FIRECRAWL_API_KEY`; crawl credits. Discover actual tool schemas before calling. |
| Matomo | `extensions/matomo/skills/seo-matomo/SKILL.md` | Translate launcher, credential setup instructions, and extension-only `seo-matomo` agent. | Environment `MATOMO_URL`, `MATOMO_API_TOKEN`, optional `MATOMO_SITE_ID`, or supported existing credential file; Reporting API requires view access. |
| Profound | `extensions/profound/skills/seo-profound/SKILL.md` | Preserve provider workflow as conditional guidance. Replace credential-file inspection with presence checks. | `PROFOUND_API_KEY` alone is insufficient. No bundled API endpoint, script, or MCP server implements the routing table. User must connect a real provider tool. |
| SE Ranking | `extensions/seranking/skills/seo-seranking/SKILL.md` | Preserve provider workflow as conditional guidance. Replace credential-file inspection with presence checks. | `SERANKING_API_KEY` alone is insufficient. No bundled API endpoint, script, or MCP server implements the routing table. User must connect a real provider tool. |
| Unlighthouse | `extensions/unlighthouse/skills/seo-unlighthouse/SKILL.md` | Run existing `unlighthouse_run.py`. Replace Claude skill copy installer with Codex skill installation. | Node and npx; the wrapper uses pinned `unlighthouse@0.13.5`. It creates a CLI config with route cap and task timeout, and bounds the subprocess. |

The DataForSEO installer enables `SERP,KEYWORDS_DATA,ONPAGE,DATAFORSEO_LABS,BACKLINKS,DOMAIN_ANALYTICS,BUSINESS_DATA,CONTENT_ANALYSIS,AI_OPTIMIZATION` and gives `FIELD_CONFIG_PATH` the absolute extension field-config path. The Codex configuration must provide a resolved real path, not an unexpanded plugin token.

Extension agents are `seo-image-gen`, `seo-dataforseo`, and `seo-matomo`. Image-gen and DataForSEO duplicate core agents. Matomo adds the twentieth unique agent procedure. The image agent is analysis-only and must never auto-generate. DataForSEO's agent fails closed if MCP is missing and explicitly forbids inspecting credentials or bypassing MCP with HTTP. Matomo's agent writes assigned findings only and reports missing credential variable names.


## Source contracts retained

Runtime state and the DataForSEO cost ledger use separate Codex directories. Credential files under `~/.config/claude-seo/`, drift baselines under `~/.cache/claude-seo/drift/`, and Banana provider data remain compatible shared paths. The package does not claim complete credential or cache isolation.

Original SSRF, DNS-rebinding, redaction, setup rollback, and script allowlist code is retained. Provider responses and fetched pages remain untrusted. The source map also records maintenance scripts, but the Codex adapter does not expose them as installed-package commands.

FLOW prompt files and their SHA-256 lock remain byte-identical source material with CC BY 4.0 credit. Some upstream prompt bodies share generic text despite distinct filenames. Their SEO content has not been rewritten as part of this host conversion.
