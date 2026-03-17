# Eleanore's Claude Context

This file is read automatically at the start of every Claude Code session in this repo. It provides global context so Claude doesn't need to be re-oriented each time.

---

## About me

- **Name**: Yi Jin (Eleanore)
- **Team**: Feature Engineering Platform (FEP) — DoorDash
- **Role**: Building and maintaining ML feature infrastructure

## My stack

| Layer | Tools |
|-------|-------|
| Data warehouse | Snowflake, Trino |
| Compute | Databricks, Kubernetes (cell-001 to cell-004) |
| Orchestration | Spinnaker (deploys), Flyte (ML pipelines) |
| Project management | Jira |
| Infra/observability | Internal MCPs (observability, reliability, compute, infra) |
| Collaboration | Slack, Google Workspace, Atlassian Confluence |
| Code | Python (primary), SQL |

## Active MCPs

See `mcps/README.md` for the full catalog and setup instructions. Key ones:

| MCP | What it does |
|-----|-------------|
| observability-mcp | Metrics, dashboards, alerts |
| ReliabilityMCP | Incident and reliability platform |
| ComputeMCP | Compute resource management |
| InfraMCP | Infrastructure graph queries |
| user-github | GitHub API — repos, PRs, issues |
| atlassian | Jira + Confluence (OAuth) |
| slack | Slack read/search |
| data-mobility | Local data mobility service |
| glean | Search all company docs + Glean AI |
| datahub | Data catalog — schemas, lineage |
| experimentation | Feature flags, DVs, Curie experiments |
| chronosphere | PromQL, SLOs, traces, logs (PAT — renew monthly) |
| granola | Meeting notes and transcripts |
| google-workspace | Google Docs, Sheets, Drive, Calendar |
| grafana | Grafana dashboards, logs, Prometheus |
| dd-etl | Test ETL DAGs with Databricks monitoring |

## Active plugins (from my-skills-marketplace)

- **snowflake** — query Snowflake via PAT token
- **databricks** — manage Databricks jobs and workflows
- **jira** — retrieve and create Jira tickets
- **trino** — query Trino at trino.doordash.team
- **spinnaker** — trigger Spinnaker pipeline deployments
- **cone** — ConductorOne group management
- **be-service-current-deploy-versions** — check deployed versions across prod cells
- **jira-report** — generate PM progress reports from Jira epics

## This repo

`eleanore-skills` is my personal skills repo. It lives alongside `doordash/my-skills` (company-wide) and `feature-engineering-platform-team/claude-code` (FEP team). Things go here when they're personal workflows or not ready to share broadly.

See `README.md` for repo structure and setup instructions.
