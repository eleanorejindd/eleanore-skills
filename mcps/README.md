# MCP Catalog

All MCP servers in use or available to add. For the full config block to paste into a new machine, see `settings-snippet.json`.

Reference: [doordash/data-agents-toolkit](https://github.com/doordash/data-agents-toolkit) — install script, full setup guides, and source code for all DoorDash MCPs.

---

## Status overview

| MCP | Type | Status | Auth |
|-----|------|--------|------|
| observability-mcp | Hosted HTTP | ✅ Active | VPN only |
| ReliabilityMCP | Hosted HTTP | ✅ Active | VPN only |
| ComputeMCP | Hosted HTTP | ✅ Active | VPN only |
| InfraMCP | Hosted HTTP | ✅ Active | VPN only |
| ai-assist | Hosted HTTP | ✅ Active | VPN only |
| data-mobility | Hosted HTTP (local) | ✅ Active | None (localhost) |
| user-github | stdio (npx) | ✅ Active | PAT |
| atlassian | stdio (npx mcp-remote) | ✅ Active | OAuth (browser) |
| slack | Hosted HTTP | ✅ Active | OAuth (CLIENT_ID) |
| glean | Hosted HTTP | ✅ Active | VPN only |
| datahub | Hosted HTTP | ✅ Active | VPN only |
| experimentation | Hosted HTTP | ✅ Active | VPN only |
| chronosphere | Hosted HTTP | ✅ Active | PAT (30-day expiry) |
| granola | Hosted HTTP | ✅ Active | OAuth (browser, one-time) |
| google-workspace | Local (Node.js) | ✅ Active | gcloud OAuth (one-time) |
| grafana | Local (Node.js) | ✅ Active | Browser session (auto-rotates) |
| dd-etl | Local (Python/conda) | ✅ Active | AWS + Databricks CLI |

---

## Hosted MCPs — zero setup (VPN only)

These work immediately on VPN. No tokens, no installation.

### observability-mcp
- **URL**: `https://cybertron-service-gateway-mcp.doordash.team/observability-mcp/mcp`
- **What it does**: Metrics, dashboards, alerts

### ReliabilityMCP
- **URL**: `https://cybertron-service-gateway-mcp.doordash.team/reliability-platform-mcp-server/mcp`
- **What it does**: Incident management and reliability platform

### ComputeMCP
- **URL**: `https://cybertron-service-gateway-mcp.doordash.team/compute-mcp/mcp`
- **What it does**: Compute resource management and right-sizing

### InfraMCP
- **URL**: `https://cybertron-service-gateway-mcp.doordash.team/infra-graph/mcp`
- **What it does**: Infrastructure graph queries

### ai-assist
- **URL**: `http://ai-assist-mcp.service.prod.ddsd:8000/sse`
- **What it does**: Internal AI assist service

### glean
- **URL**: `https://doordash-be.glean.com/mcp/default`
- **What it does**: Search all company docs, wikis, Confluence pages; chat with Glean AI via RAG; look up people profiles

### datahub
- **URL**: `https://cybertron-service-gateway-mcp.doordash.team/datahub/mcp`
- **What it does**: Data catalog — search datasets, tables, columns; view schemas, ownership, lineage, documentation

### experimentation
- **URL**: `https://cybertron-service-gateway-mcp.doordash.team/experimentation/mcp`
- **What it does**: Feature flags, Dynamic Values (DVs), Curie experiment results, guardrail metrics

---

## Hosted MCPs — need token or OAuth

### data-mobility
- **URL**: `http://localhost:8080/mcp`
- **What it does**: Local data mobility service — must be running locally first
- **Note**: Start the service before use; localhost only

### user-github
- **Command**: `npx @modelcontextprotocol/server-github`
- **What it does**: GitHub API — repos, PRs, issues, code search
- **Auth**: `GITHUB_PERSONAL_ACCESS_TOKEN` env var
- **Setup**: Generate a PAT at https://github.com/settings/tokens (needs `repo`, `read:org` scopes)

### atlassian
- **Command**: `npx mcp-remote https://mcp.atlassian.com/v1/sse`
- **What it does**: Jira + Confluence via Atlassian's official MCP (Rovo AI included)
- **Auth**: OAuth via browser (one-time; prompts on first run)

### slack
- **URL**: `https://mcp.slack.com/mcp`
- **What it does**: Slack read/search — messages, channels, threads
- **Auth**: OAuth with CLIENT_ID; requires session token in headers

### chronosphere
- **URL**: `https://doordash.chronosphere.io/api/mcp/mcp`
- **What it does**: PromQL queries, SLOs, distributed traces, logs, monitors, dashboards
- **Auth**: Personal Access Token (expires every 30 days)
- **Setup**:
  1. Go to doordash.chronosphere.io → profile icon → My Account → Add Token
  2. Name it (e.g. `claude-code-mcp`), set expiry (max 30 days), copy token
  3. Add to `headers: { "API-Token": "<token>" }` in settings.json
  4. **Reminder**: token expires — set a calendar reminder to regenerate monthly
- **Note**: Prefer Chronosphere over Grafana for SLOs and traces; use Grafana for DoorDash-specific log indexes

### granola
- **URL**: `https://mcp.granola.ai/mcp`
- **What it does**: Meeting notes, transcripts, AI summaries, action items
- **Auth**: Browser OAuth (one-time; no VPN required)
- **Setup**: After adding to settings.json, Claude Code will prompt for OAuth on first use. Requires Granola desktop app installed and syncing.

---

## Local MCPs — require local build/install

### google-workspace
- **What it does**: Google Docs (read/write/format), Sheets, Drive, Calendar
- **Auth**: gcloud OAuth (one-time setup ~5 min)
- **Setup**:
  ```bash
  cd ~/Projects/data-agents-toolkit/mcps/google-workspace
  npm install && npm run build
  brew install --cask google-cloud-sdk  # if not installed
  gcloud auth login
  ./setup-gcloud.sh  # opens browser twice for OAuth consent
  ```
- **Config**: Points to `dist/index.js` in the built directory (see `settings-snippet.json`)

### grafana
- **What it does**: Search Grafana dashboards, query Prometheus/PromQL, query DoorDash application logs, list alerts and annotations
- **Auth**: Browser session (auto-rotates every 8 min; re-run `npm run auth` when expired)
- **Setup**:
  ```bash
  cd ~/Projects/data-agents-toolkit/mcps/grafana
  npm install && npm run build
  npx playwright install chromium  # one-time, ~150MB download
  npm run auth  # opens browser for SSO login; repeat when session expires
  ```
- **Config**: Points to `dist/index.js` + `GRAFANA_URL` env var (see `settings-snippet.json`)
- **Note**: Use for DoorDash-specific log indexes. Use Chronosphere for SLOs and traces.

### dd-etl
- **What it does**: Test DoorDash ETL DAGs locally with real-time progress tracking and Databricks job monitoring
- **Auth**: AWS CLI (okta-prod-engineer profile) + Databricks CLI (doordash-dataeng profile)
- **Prerequisites**: Miniconda, Docker Desktop, AWS CLI, Databricks CLI, `doordash-etl` repo cloned
- **Setup**:
  ```bash
  conda create -n dd-etl python=3.12 -y
  conda activate dd-etl
  cd ~/Projects/data-agents-toolkit/mcps/dd-etl
  pip install -r requirements.txt
  ```
- **Config**: Requires conda env Python path + your DD ETL username (see `settings-snippet.json`)
- **Full guide**: See [mcps/dd-etl/README.md](https://github.com/doordash/data-agents-toolkit/blob/main/mcps/dd-etl/README.md)

---

## Custom MCPs

Add custom MCP servers you build to `custom/`. Each gets its own subdirectory with a README explaining what it does and how to run it.

```
mcps/custom/
└── {mcp-server-name}/
    ├── README.md
    ├── server.py (or index.ts, etc.)
    └── ...
```
