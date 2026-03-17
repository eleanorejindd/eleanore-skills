# Pedregal Bi-Weekly Status

Generates the Project Pedregal Data Platform bi-weekly summary using the standing
Google Doc format, Slack release/status signals, and Jira status context.

## Skills

| Skill | What it does |
|-------|--------------|
| `pedregal-biweekly-status` | Builds a past-14-days Data Platform summary, asks Yi Jin for blockers and thread pointers, and optionally writes the approved draft to the status doc. |

## Auth / Setup

This plugin relies on MCP access to:

- Google Workspace for reading the format doc and optionally editing it after approval
- Slack for reading `#pedregal-data-platform-comms`
- Jira for issue status and cross-checking current progress

## Key files

- `skills/pedregal-biweekly-status/SKILL.md` - main skill definition

## Notes

- The skill must always ask Yi Jin for blockers, missing context, and any threads or
  documents to include before finalizing.
- Google Doc writes always require an explicit preview and confirmation.
