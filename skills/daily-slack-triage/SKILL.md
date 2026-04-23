---
name: daily-slack-triage
description: >
  Scans Slack for threads where Yi Jin (Eleanore) has been @-mentioned in the
  last 3 days but hasn't replied, or replied but new follow-ups have landed,
  then posts a single prioritized digest to her own Slack DM. Ranks by urgency
  (P0 / P1 / P2) first, then sub-groups by category: Pedregal launch blocker
  (dependencies from Eradinus, Nexus, or other platform teams), reliability
  issue, Pedregal feature gap / bug, support escalation, or other. Use when
  Yi Jin says "run my daily slack triage", "triage my slack", "what slack
  threads need my attention", "send me my slack digest", "what did I miss in
  slack", "who is waiting on me in slack", or schedules this as a recurring
  task (intended to run weekdays at 5pm PT). Does not reply to any source
  thread — the only outbound action is the self-DM summary.
---

# Daily Slack Triage

A single end-of-day Slack DM that tells Yi Jin which tagged threads still need
her attention, ranked by urgency, so nothing falls through the cracks before
she signs off. Specifically tuned to surface Pedregal launch blockers coming
from platform dependencies (Eradinus, Nexus) alongside general support,
reliability, and bug signals.

## When to use

- **Recurring end-of-day check** — the intended default; a scheduled run at
  5pm PT weekdays produces the digest.
- **Ad-hoc catch-up** — "what did I miss today", "who's waiting on me",
  "triage my slack" outside the scheduled time.
- **After extended focus time or PTO** — widen the lookback window (e.g. last
  7 days) by telling the skill how far back to look.

## When NOT to use

- Single-thread debriefs → use `summarize-slack-thread` instead.
- Weekly Pedregal status doc updates → use `pedregal-biweekly-status`.
- Drafting replies or taking action inside threads — this skill is
  read-and-summarize only.

## Inputs and defaults

| Input | Default | Notes |
|-------|---------|-------|
| Lookback window | 3 days (72 hours) | Override with "look back N days" |
| Destination | Yi Jin's Slack self-DM | Do not post anywhere else |
| Run cadence | Weekdays ~5pm PT | When scheduled |
| User identity | Email `yi.jin@doordash.com` → Slack ID | Resolve fresh each run |

## Workflow

### 1. Load Slack auth + resolve identity

Before any Slack operation, make sure the Slack CLI is ready. In Cowork, the
`slack` CLI auto-provisions via the desktop bridge — no precheck needed. If a
call stalls and the output contains `[bridge] auth`, tell Yi Jin:

> "A browser window should have opened on your Mac for authentication.
> Please complete the sign-in there."

Resolve Yi Jin's Slack user ID from her email:

```bash
slack search_users --email yi.jin@doordash.com
```

Store the returned user ID as `$USER_ID`. All subsequent searches and the
final DM target this ID.

### 2. Gather candidate threads (last 3 days)

Collect from three sources, dedupe by thread permalink at the end.

**a. @-mentions in public channels**

```bash
slack search_public --query "<@$USER_ID>" --after "$(date -v-3d +%Y-%m-%d)"
```

**b. Unreplied DMs and group DMs**

List recent DM conversations; keep only ones whose last message is NOT from
`$USER_ID`.

**c. Threads she already posted in that have new replies**

For each recent thread she's participated in, use `slack read_thread` to
check whether any message was posted after her last message.

### 3. Filter to unresolved only

For every candidate, read the full thread and keep it only if:

- **🆕 no reply yet** — she has NOT replied at all, OR
- **↩️ new follow-up since your reply** — she replied but there is at least
  one message from someone else after her last reply.

Drop:

- Threads where her last message was the final word and nothing has happened
  since.
- Bot pings / automation messages that don't need a human reply.
- Channel-wide `@here` / `@channel` announcements where she wasn't
  specifically addressed.

### 4. Categorize each thread into exactly one bucket

Use the first match, top to bottom (launch blocker beats reliability beats
bug beats support beats other):

1. **Pedregal launch blocker** — items blocking the Pedregal product launch,
   especially from platform dependencies (Eradinus, Nexus, or other
   infra/platform teams). Signal words: `blocker`, `blocking launch`,
   `launch dependency`, plus dependency team names.
2. **Reliability issue** — incidents, outages, latency spikes, error-rate
   regressions, SLO burns, on-call pages. May or may not be Pedregal-specific.
3. **Pedregal feature gap / bug** — bug reports, feature requests, or
   functional issues tied to Pedregal. Channel name contains `pedregal` or
   the thread mentions Pedregal features/screens/flows.
4. **Support escalation** — threads from support/escalation channels
   (`#cx-*`, `#support-*`, `#eng-escalations`, `#help-*`) or any ask tied to
   a customer / merchant / Dasher-impacting issue needing triage.
5. **Other** — anything that doesn't fit the above four.

Match case-insensitively. Pedregal signal words: `pedregal`, `eradinus`,
`nexus` (the DoorDash platform, not the general word), explicit Pedregal
launch-milestone references.

### 5. Assign an urgency tag (P0 / P1 / P2)

- **P0 — Urgent.** Active incident language (`down`, `outage`, `customers
  impacted`, `blocking launch`, on-call pages, `urgent`, `ASAP`), direct asks
  from senior leaders, launch blockers flagged as critical.
- **P1 — Needs response today.** Important stakeholder asking a direct
  question, unresolved blockers not yet critical, threads with 2+ follow-ups
  poking for a response.
- **P2 — FYI / low urgency.** Informational tags, non-urgent questions,
  asks with no deadline.

When in doubt, prefer the higher urgency (err toward P1 over P2).

### 6. Compose the DM — urgency first, then category

```
📬 Daily Slack triage for <YYYY-MM-DD> — <N> unresolved threads

🚨 *P0 — Urgent (<count>)*
• [<category>] <one-sentence summary ≤120 chars> — #<channel> — tagged by <display name> — <🆕 | ↩️> — <slack permalink>
• ...

⚠️ *P1 — Needs response today (<count>)*
• [<category>] ...

ℹ️ *P2 — FYI / low urgency (<count>)*
• [<category>] ...
```

Within each urgency tier, sub-group by category in this order:

1. Pedregal launch blocker
2. Reliability issue
3. Pedregal feature gap / bug
4. Support escalation
5. Other

Per-item constraints:

- Summary ≤120 chars, plain text, no jargon explosion.
- Channel name as `#channel-name`, not channel ID.
- Tagger = display name, not user ID.
- Permalink preserved exactly — this is how Yi Jin jumps into the thread.
- Status glyph: `🆕` for no reply yet, `↩️` for new follow-up since her reply.

### 7. Send the DM

Open (or reuse) a self-DM conversation with `$USER_ID` and post the summary
using `slack send_message` with Slack mrkdwn formatting.

If the digest would exceed ~35,000 chars (Slack's hard limit is 40k),
truncate the P2 section first and append:

> `(<X> more P2 items not shown — widen the window or ask me to paginate)`

### 8. Empty-inbox case

If there are zero unresolved threads, still send a short DM:

> `✅ Inbox zero — no unresolved tagged threads from the last 3 days. Nice.`

## Output format Yi Jin can expect

```
📬 Daily Slack triage for 2026-04-23 — 7 unresolved threads

🚨 *P0 — Urgent (2)*
• [Pedregal launch blocker] Eradinus team needs auth decision by EOD — #pedregal-launch — tagged by Alex Chen — ↩️ — <link>
• [Reliability issue] Checkout p99 latency spiked 4x — #reliability — tagged by Sam Wu — 🆕 — <link>

⚠️ *P1 — Needs response today (3)*
• [Pedregal feature gap / bug] Cart page crash on iOS 17 — #pedregal-bugs — tagged by Jordan Lee — 🆕 — <link>
• [Support escalation] Merchant can't onboard — #cx-merchants — tagged by Priya Shah — ↩️ — <link>
• [Other] PM asking for roadmap input — #pm-roundtable — tagged by Chris Ng — 🆕 — <link>

ℹ️ *P2 — FYI / low urgency (2)*
• [Pedregal feature gap / bug] FYI: filter edge case — #pedregal-bugs — tagged by Taylor R — 🆕 — <link>
• [Other] Doc review request — #pedregal-pm — tagged by Morgan Q — 🆕 — <link>
```

## Constraints

- **Never post outside Yi Jin's self-DM.** No replies, reactions, or
  messages in source threads.
- **Never skip the skill load + identity resolution steps.** Auth and the
  user ID must be resolved before searches.
- **Preserve permalinks verbatim.** They are the primary navigation aid.
- **Categorization is best-guess** — if ambiguous, prefer the more urgent
  category (launch blocker > reliability > bug > support > other).
- **Do not persist state between runs.** Each run is independent; the
  digest reflects the current 3-day window at run time.

## Error handling

- Slack search returns empty across all sources → still send the
  "✅ Inbox zero" DM so Yi Jin knows the run completed.
- Slack auth fails silently → surface a notification: "Slack auth may be
  stale — open the Cowork bridge browser tab on your Mac to re-sign-in."
- A thread permalink can't be generated → include the `channel_id + ts`
  pair so she can still navigate manually.
- DM send fails → leave the composed digest in the run output so it can be
  retried manually.

## Related skills

- `summarize-slack-thread` — deep-dive on a single flagged thread.
- `pedregal-biweekly-status` — for the 2-week Pedregal Data Platform doc.
- `pedregal-mob-weekly-update` — for the weekly MOB tracker post.
