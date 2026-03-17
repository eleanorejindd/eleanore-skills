# eleanore-skills

Personal Claude Code skills and MCP catalog for daily work at DoorDash.

---

## What's in here

| Directory | Purpose |
|-----------|---------|
| `.cursor/skills/` | Cursor-discoverable symlinks to skills in `skills/` |
| `plugins/` | Multi-skill plugins — when a domain needs several skills + agents bundled together |
| `skills/` | Simple standalone skills — single-purpose, no plugin wrapper needed |
| `mcps/` | MCP catalog and config — documents all MCP servers in use, settings snippet for new machine setup |
| `packages/` | Shared Python libraries reused across multiple plugins/skills |

---

## How skills and plugins work

**Skills** are the basic unit. Each skill is a folder with a `SKILL.md` file (YAML frontmatter + instructions) and optionally a `scripts/` subdirectory with Python scripts Claude can execute.

In this repo, the **source of truth** for repo-local skills lives under `skills/`. If a skill should be directly discoverable by Cursor, create a directory symlink in `.cursor/skills/` that points back to `skills/{skill-name}`. Do not duplicate the skill contents in both places.

**Plugins** are bundles: one or more skills + optional agents, versioned together. Use a plugin when:
- You have 2+ related skills that share code, auth, or context
- You want agents alongside the skills
- You want versioning and a changelog

For simple one-off automations, a standalone skill in `skills/` is fine.

---

## Directory structure

```
eleanore-skills/
│
├── README.md                        ← you are here
├── CLAUDE.md                        ← global context Claude reads in every session
│
├── .cursor/
│   ├── rules/                       ← persistent Cursor rules for this repo
│   └── skills/
│       └── {skill-name} -> ../../skills/{skill-name}
│                                     ← symlink for Cursor skill discovery
│
├── .claude-plugin/
│   └── marketplace.json             ← registers this repo as a personal marketplace
│
├── plugins/
│   └── {plugin-name}/
│       ├── .claude-plugin/
│       │   └── plugin.json          ← name, description, version
│       ├── CLAUDE.md                ← plugin-specific docs and usage notes
│       ├── skills/
│       │   └── {skill-name}/
│       │       ├── SKILL.md         ← skill definition (frontmatter + instructions)
│       │       └── scripts/         ← Python scripts the skill calls
│       └── agents/                  ← (optional) autonomous agent definitions
│
├── skills/
│   └── {skill-name}/
│       ├── SKILL.md
│       └── scripts/
│
├── mcps/
│   ├── README.md                    ← catalog of all MCPs in use
│   ├── settings-snippet.json        ← mcpServers block to paste into ~/.claude/settings.json
│   └── custom/                      ← custom MCP servers you build yourself
│       └── {mcp-server-name}/
│
├── packages/
│   └── {shared-lib}/                ← shared Python code used by multiple plugins
│
└── pyproject.toml                   ← code quality config (ruff)
```

---

## Setup on a new machine

### 1. Register this repo as your personal marketplace

```bash
# In a Claude Code session:
/plugin marketplace add path/to/eleanore-skills
# or if published to GitHub:
/plugin marketplace add eleanorejindd/eleanore-skills
```

### 2. Install your plugins

```bash
/plugin install {plugin-name}@eleanore-skills
```

### 3. Restore MCP configuration

Copy the `mcpServers` block from `mcps/settings-snippet.json` into `~/.claude/settings.json`.
See `mcps/README.md` for per-MCP setup instructions (auth, tokens, etc.).

---

## Adding a new skill

1. Create the canonical skill at `skills/{skill-name}/SKILL.md`
2. Use a concise skill name; avoid prefixes like `dmf-` unless there is a strong reason to keep one
3. If the skill should be directly discoverable in Cursor, symlink `.cursor/skills/{skill-name}` to `../../skills/{skill-name}`
4. For a **plugin**: copy `plugins/_template/` and fill in the blanks
5. If it's in a plugin, bump the version in `plugin.json` AND `marketplace.json`
6. Run `/plugin marketplace update` and reload the Claude Code session

---

## Current plugins and skills

| Name | Type | What it does |
|------|------|--------------|
| `pedregal-biweekly-status` | Skill | Builds the Pedregal Data Platform bi-weekly update from Slack, Jira, and Google Docs context |
| `google-docs` | Skill | Read, search, and update Google Docs with local OAuth-backed scripts |
| `google-sheets` | Skill | Read, create, and update Google Sheets with local OAuth-backed scripts |
| `pedregal-biweekly-status` | Plugin | Plugin wrapper for the Pedregal bi-weekly status workflow |

Update this table as you add things.
