---
name: pedregal-mob-weekly-update
description: >
  Posts the weekly MOB (Migration Operations Backlog) status update to Slack
  channel #pedregal-data-mob. Reads the Pedregal user-reported issues Google Doc,
  queries Jira for all dp-de-mob labeled tickets, then posts a structured summary
  showing closed tickets, in-progress tickets, to-do tickets, and open doc items
  that haven't been filed as Jira tickets yet. Use every Wednesday at 10 AM PST, or whenever
  asked for the MOB weekly update, Pedregal MOB status, dp-de-mob summary, user
  issues weekly post, or "post to pedregal-data-mob".
---

# Pedregal MOB Weekly Status Update

Post a concise weekly snapshot to `#pedregal-data-mob` covering Jira ticket
progress and open items from the user-reported issues tracking doc.

## Key references

| What | Value |
|------|-------|
| Google Doc (issues tracker) | `1ECGZkTVx_YiZ22Q4L12YogzLd_I_a-t414jOLKxPfuI` |
| Jira label | `dp-de-mob` |
| Jira dashboard | `https://doordash.atlassian.net/jira/dashboards/48389` |
| Slack channel | `#pedregal-data-mob` (channel ID: `C0AHH51C81J`) |

---

## Workflow

### 1. Read the Google Doc — all content tabs

The doc has 6 tabs. Skip the JIRA board tab; read the other 5 in parallel.

```
googleDoc action=listTabs
  documentId=1ECGZkTVx_YiZ22Q4L12YogzLd_I_a-t414jOLKxPfuI
```

Then read each content tab in parallel (skip tab ID `t.1lv26191222i` = "JIRA board"):

| Tab name | Tab ID |
|----------|--------|
| Derived Dataset | `t.0` |
| External Data Asset | `t.5mf24fbr2bl6` |
| Data Compute (Spark) | `t.8nep931w92il` |
| Offline to Online (OtO) | `t.8rsxn3ihcvj5` |
| Data Control Plane (DCP) | `t.pl3c8mxvpzuj` |

```
googleDoc action=read
  documentId=1ECGZkTVx_YiZ22Q4L12YogzLd_I_a-t414jOLKxPfuI
  format=markdown
  tabId=<each tab ID above>
```

For each entry across all tabs, extract these fields:

| Field | Doc label |
|-------|-----------|
| Status | `Status:` |
| Reporter | `Reporter:` |
| Date | `Time reported:` |
| Domain | `Domain:` — e.g. Derived Dataset, External Asset, OtO, Data Compute, DCP |
| Scenario | `Describe the scenario:` — keep to 1-2 sentences |
| Jira link | `Jira Link:` — may be empty or contain a ticket key like `FRAMEWORKS-227` |

**Skip** any entry where Scenario, Reporter, and Date are all blank — these are
unfilled template copies.

**Skip** struck-through entries (visually indicated in the doc as deleted items).

### 2. Query Jira — run all four queries in parallel

**Closed (past 7 days):**
```jql
labels = "dp-de-mob" AND statusCategory = Done AND updated >= -7d ORDER BY updated DESC
```

**In Progress:**
```jql
labels = "dp-de-mob" AND status = "In Progress" ORDER BY updated DESC
```

**To Do:**
```jql
labels = "dp-de-mob" AND statusCategory = "To Do" ORDER BY updated DESC
```

**All tickets (for total count):**
```jql
labels = "dp-de-mob" ORDER BY updated DESC
```

Pull fields: `key`, `summary`, `status`, `priority`, `assignee`, `duedate`.

**Exclude** the sample task ticket `DMI-261` ("MoB Sample Task") from all sections.

**Priority normalization**: extract the P-level from any format:
- "Critical (P0)", "P0 (Show Stopper)" → P0
- "Major (P1)", "P1" → P1
- "Normal (P2)", "P2 (Important)" → P2

### 3. Identify open doc items with no Jira ticket

From the doc entries in step 1, find those where the Jira Link field is empty or missing.

**Cross-reference against Jira**: some entries look ticket-less in the doc but are already
filed. Match entries by keyword similarity against the summaries of all dp-de-mob Jira
tickets. If a strong match exists, treat that entry as already filed and exclude it from
open items.

**Skip** any entry where Status is "decide to close" or any close-intent value.

For each remaining entry, capture:
- **Domain**: the Domain field value; use `-` if blank
- **Status**: the Status field value; use `-` if blank
- **Scenario**: first 1-2 sentences — keep very short (<=8 words)
- **Reporter**: the Reporter name; use `reporter unknown` if blank
- **Date**: the Time reported value; use `date unknown` if blank

If Date and Reporter are **both** blank, omit the entry (likely a partial template copy).

### 4. Compute overall counts

- **Total** `dp-de-mob` tickets (all time, excluding DMI-261)
- **Closed this week** [M]: count from the past-7-day closed query
- **Closed all-time** [N]: count of Done-category tickets from the all-tickets query
- **In Progress**: count
- **To Do**: count
- **Open (no ticket)**: count of qualifying doc entries

The closed table shows only this week's tickets (from the past-7-day query).
The all-time count appears in the section header and overall line for historical context.

### 5. Draft and post the Slack message

Use this format. All tabular sections use triple-backtick code blocks (Slack does not
render markdown tables natively).

    📊 *Pedregal MOB Weekly Update - [Day, Month Date]*

    *Overall:* [Total] total tickets | ✅ [M] this week / [N] all-time closed | 🔄 [N] in progress | 📋 [N] to do | 📝 [N] open (no ticket yet)

    ✅ *Closed this week ([M]) - [N] all-time*
    ```
    Key             | P  | Summary                        | DRI
    ----------------+----+--------------------------------+----------------
    DMI-414         | P0 | Hardcoded SP in src checker    | Jason Chin
    DMI-399         | P2 | Document DBs for DD ext assets | Eleanore Jin
    ```

    🔄 *In Progress*
    ```
    Key             | P  | Summary                        | DRI          | Due
    ----------------+----+--------------------------------+--------------+----------
    DMI-397         | P0 | No col projection for ext asset| Jason Chin   | 2026-04-03
    FRAMEWORKS-217  | P1 | Date macros for incr. loads    | Hadi Zhang   | 2026-03-31
    ```

    📋 *To Do (filed, not started)*
    ```
    Key             | P  | Summary                        | DRI          | Due
    ----------------+----+--------------------------------+--------------+----------
    FRAMEWORKS-224  | P1 | Mandatory created/modified_at  | Gangadhar R. | 2026-03-31
    DMI-431         | P2 | EA linter blocks PII assets    | no assignee  | -
    ```

    📝 *Open items - no Jira filed yet*
    ```
    Domain          | Status | Scenario                       | Reporter        | Date
    ----------------+--------+--------------------------------+-----------------+------------
    Derived Dataset | -      | 403 error despite Tailscale    | reporter unknown| 5th Mar 2026
    External Asset  | -      | Lint checks skip src table     | Alex Prosak     | Mar 5, 2026
    ```

    🔗 <https://doordash.atlassian.net/jira/dashboards/48389|Jira dashboard>

Formatting rules:
- Omit any section whose list is empty — don't show a header with nothing under it
- Slack code blocks wrap at ~80 chars per line — keep every row under 80 chars total
- Column widths for ticket tables: Key=16, P=3, Summary=32, DRI=14, Due=10
- Column widths for open items: Domain=16, Status=8, Scenario=32, Reporter=17, Date=12
- Truncate Summary and Scenario aggressively to fit — aim for <=30 chars, append "..." only if truly needed
- Use Jira ticket keys not full URLs; abbreviate `FRAMEWORKS-` as `DMF-` for display (e.g., `FRAMEWORKS-217` -> `DMF-217`)
- If assignee is null/unassigned, write `no assignee`; if due date absent, write `-`
- Slack bold = `*text*`, italic = `_text_`, link = `<url|label>`
- Avoid em dashes and `---` separators — Slack's block parser rejects them; use plain hyphens

Post directly to Slack without asking for confirmation:

```
slack_send_message
  channel_id=C0AHH51C81J
  message=<the formatted message>
```

---

## Scheduling this weekly

This skill runs every Wednesday at 10 AM PST via a macOS cron job.

**Cron setup** (one-time):

```bash
crontab -e
```

Add this line:

```
0 10 * * 3 cd /Users/yi.jin/Projects/eleanore-skills && /Users/yi.jin/.local/bin/claude --dangerously-skip-permissions -p "/pedregal-mob-weekly-update" >> /tmp/mob-weekly-update.log 2>&1
```

Check logs after first run: `tail -f /tmp/mob-weekly-update.log`

Note: cron won't run if the Mac is asleep at 10 AM. For reliable delivery, either keep
the machine awake on Wednesdays or use a launchd agent instead.

---

## Error handling

- **Doc read fails**: Try again once; if it still fails, post a message to the channel
  saying the update is delayed and include the Jira dashboard link.
- **Jira query returns no results**: Post a message noting "no dp-de-mob tickets found"
  with the dashboard link for manual review.
- **Slack post fails**: Print the formatted message to stdout so it appears in logs.
- **Reporter / Date missing from doc entry**: Include the scenario but write
  `reporter unknown` / `date unknown` rather than skipping it.
