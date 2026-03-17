---
name: pedregal-biweekly-status
description: >
  Summarizes the last 2 weeks of Project Pedregal Data Platform work using the
  standing Google Doc as the format source, Slack channel
  #pedregal-data-platform-comms for releases and discussion, and Jira for current
  status. Use when Yi Jin asks for a Pedregal bi-weekly update, Pedregal data
  platform summary, Pedregal status doc update, or a past-2-weeks summary. This
  skill must ask Yi Jin for blockers, missing context, and any Slack threads or
  docs that should be included before finalizing.
---

# Pedregal Bi-Weekly Status Update

Prepare a Data Platform summary for the past 14 days, grounded in source links and
reviewed with Yi Jin before any Google Doc write.

## Key references

- Google Doc: `1S5N4MZjzuKr4s94heI2bjS2cIJdISwl93tDit8ip2ec`
- Google Doc bookmark fallback: `id.60sej5duj5vk`
- Slack channel: `#pedregal-data-platform-comms`
- Jira plan URL: `https://doordash.atlassian.net/jira/plans/10017/scenarios/10224/timeline?vid=12892`
- Coverage window: last 14 days unless Yi Jin asks for a different range

## Required behavior

- Always read the Google Doc first to learn the current format before drafting.
- Always collect both Slack and Jira evidence.
- Always keep source links for every important point.
- Always ask Yi Jin for blockers, missing context, and pointers to any threads,
  tickets, or docs that should be included.
- Never write to the Google Doc without showing a preview and getting explicit
  confirmation first.

## Workflow

### 1. Ask for user context first

Start by asking Yi Jin for any context that will not reliably appear in Slack or Jira:

- Any blockers or risks that should be called out
- Any Slack threads, Jira tickets, docs, or meeting notes to include
- Whether she wants only a draft in chat or also wants the Google Doc updated after review

If she provides links or ticket IDs, keep them and incorporate them into the source set.

### 2. Read the reference doc format

Use `googleDoc` in read-only mode:

1. `action: "listTabs"` for document `1S5N4MZjzuKr4s94heI2bjS2cIJdISwl93tDit8ip2ec`
2. Identify the latest-dated tab
3. `action: "read"` on that tab in `markdown` or `text`
4. Find the `Data Platform` section and copy its structure closely

Calibrate against the latest one or two prior entries for:

- Section headings
- Bullet density
- Tone and tense
- Whether links are inline or collected separately

If the document cannot be read because of permissions or structure issues, ask Yi Jin to
share access or point to the exact section, and continue by using the bookmark as a hint.

### 3. Gather Slack evidence

Use `slack_search_public` against `#pedregal-data-platform-comms` for the last 14 days.
Prefer several targeted searches over one broad search.

Recommended query patterns:

- `in:#pedregal-data-platform-comms after:YYYY-MM-DD shipped`
- `in:#pedregal-data-platform-comms after:YYYY-MM-DD release`
- `in:#pedregal-data-platform-comms after:YYYY-MM-DD blocked`
- `in:#pedregal-data-platform-comms after:YYYY-MM-DD risk`
- `in:#pedregal-data-platform-comms after:YYYY-MM-DD decision`
- `in:#pedregal-data-platform-comms after:YYYY-MM-DD next sprint`

For each promising message:

1. Save the permalink
2. Read the thread if needed with `slack_read_thread`
3. Extract only durable signal, not chatter

Group findings into:

- Progress and releases
- Decisions made
- Upcoming next steps
- Blockers and risks

### 4. Gather Jira status

Use Jira to confirm current status and cross-check what matters most for Data Platform.

Preferred approach:

- Use `jira_search` with JQL for issues updated in the last 14 days and likely related to
  Pedregal Data Platform

Good starting JQL patterns:

- `updated >= -14d AND text ~ "Pedregal" ORDER BY updated DESC`
- `updated >= -14d AND labels = pedregal ORDER BY updated DESC`
- `project in (...) AND updated >= -14d AND summary ~ "Pedregal" ORDER BY updated DESC`

If the relevant project keys or labels are unclear:

- Use the Jira plan URL as the human reference point
- Ask Yi Jin which project key, labels, or epics are the right scope
- Prefer confirmed epics/issues over guesswork

For each item you keep, capture:

- Issue key and URL
- Summary
- Current status
- Owner if relevant
- Why it belongs in the summary

### 5. Synthesize the update

Produce a concise draft that reflects the document's existing format. Prefer factual,
source-backed bullets over narrative prose.

Use this draft shape unless the doc clearly uses a different one:

```markdown
Here is the draft Data Platform update for [date range].

**Progress**
- [completed or advanced item] ([Slack or Jira link])
- [completed or advanced item] ([Slack or Jira link])

**Next Steps**
- [next step]
- [next step]

**Blockers / Risks**
- [risk or blocker] — owner if known ([Slack or Jira link])

**Sources**
- Slack: [thread 1], [thread 2]
- Jira: [ticket 1], [ticket 2]
```

Rules for synthesis:

- Do not include items without evidence unless Yi Jin explicitly supplies them
- If Yi Jin supplies an item from memory, ask whether there is a thread, ticket, or doc
  you should cite
- Omit empty sections only if the doc pattern also omits them
- Keep each bullet specific enough that a reader can understand the outcome quickly
- For shipped wins, include a short one-line explanation of what launched, changed, or was
  unblocked instead of listing only the item name

### 6. Review with Yi Jin before any write

After presenting the draft, ask:

`Are there any blockers, missing context, or updates I should add? If you have any Slack threads, Jira tickets, or docs I should reference, send them and I’ll fold them in.`

If Yi Jin gives extra context:

- Update the draft
- Add the cited link if she provides one
- If no link is available, label it as user-provided context and ask whether it should
  still be included

Only proceed to writing after she explicitly approves the final draft.

### 7. Write to the Google Doc only with confirmation

Before any edit, show:

- Action: update the Pedregal status doc
- Target: document ID `1S5N4MZjzuKr4s94heI2bjS2cIJdISwl93tDit8ip2ec`, latest-dated tab,
  `Data Platform` section
- Content: the exact final summary text to be inserted

Then ask for confirmation.

If approved:

1. Use the Google Docs write tool to insert or replace the summary in the latest-dated tab
2. Match the surrounding format exactly
3. Preserve or add inline Jira and Slack links where the doc style supports them
4. Confirm success with the doc link

If not approved or if write access fails, leave the final markdown in chat for Yi Jin to
paste manually.

## Error handling

- Cannot access the Google Doc: ask Yi Jin to share access, paste the target section, or
  confirm the expected format
- Slack searches are sparse: widen to 21 days and run narrower keyword searches
- Jira scope is unclear: ask Yi Jin for the project key, labels, epic IDs, or ticket links
- Slack and Jira disagree: prefer the most recent explicit status and call out the conflict
- No blockers found: still ask Yi Jin whether there are off-thread blockers to include
