---
name: daily-slack-triage
description: >
  Builds a persistent, checkable Slack Canvas digest of unresolved items from
  the past 1 day (24 hours) — @-mentions in both public AND private channels,
  DMs, group DMs, and threads Yi Jin (Eleanore, U02N4K114AK) authored or
  participated in where new activity has landed since her last reply
  (including threads she started where no one @-tagged her back). Posts / updates a single Canvas in her
  self-DM where she checks items off; next run reads the canvas first and
  skips anything already checked. Ranks by urgency (P0 / P1 / P2) then
  sub-groups by category: Pedregal launch blocker (Eradinus / Nexus / other
  platform-team deps), reliability issue, Pedregal feature gap / bug, support
  escalation, or other. The 1-day lookback applies uniformly to every category
  and every priority — nothing older than 24h enters the digest, regardless of
  urgency. Does not reply to or react on any source thread. Use when Yi Jin
  says "run my daily slack triage", "triage my slack", "what slack threads
  need my attention", "send me my slack digest", "who is waiting on me", or
  schedules this as a recurring weekday 5pm PT task. Also posts a daily
  decision log (markdown, date-titled) of threads that closed during the
  window — capturing problem, decision / conclusion, and decision-makers
  for each closed thread — directly to her Slack self-DM as a separate
  message after the triage notification (with Gmail fallback if Slack is
  unavailable). The skill performs no local file writes; Yi Jin archives
  the decision log content from Slack to her own knowledge base manually.
  Resilient to unattended scheduled runs: pre-flight auth check with a
  hard 5-second budget so the run never hangs waiting for browser sign-in;
  on Slack-auth failure, sends an email to yi.jin@doordash.com instead.
---

# Daily Slack Triage

A single end-of-day **interactive Canvas** in Yi Jin's self-DM that tracks
which tagged threads still need her attention. She ticks items off inside
Slack; subsequent runs respect those checks and only surface new unresolved
activity.

## When to use

- **Recurring end-of-day check** — the intended default; scheduled weekdays
  at 5pm PT.
- **Ad-hoc catch-up** — "what did I miss today", "who's waiting on me",
  "triage my slack".

## When NOT to use

- Single-thread debriefs → use `summarize-slack-thread`.
- Weekly Pedregal status doc updates → use `pedregal-biweekly-status`.
- Drafting replies or acting inside threads — this skill is read-and-summarize
  only.

## Inputs and defaults

| Input | Default | Notes |
|-------|---------|-------|
| Lookback window | **1 day (24 hours)** | Strict, uniform across every category and priority. Do not override. |
| Triage destination | Self-DM canvas titled `Daily Slack Triage — @eleanore.jin` | Re-used across runs; never create a second one |
| Decision log destination | Slack self-DM (separate message after triage notification) | Eleanore archives to her local knowledge base manually |
| Failure-notification fallback | Gmail to yi.jin@doordash.com | Used when Slack auth is broken |
| Pre-flight auth budget | 5 seconds | Hard timeout — fail fast in unattended runs, never wait for browser auth |
| Run cadence | Weekdays ~5pm PT | When scheduled |
| User identity | Email `yi.jin@doordash.com` → Slack ID `U02N4K114AK` | Resolve fresh each run |
| Local file writes | **None** | Skill writes nothing to local disk; everything goes to Slack or Gmail |

## Output format — Slack Canvas with interactive checkboxes

The digest is posted as a **Slack Canvas** (not a plain message). Canvases:

- Render `- [ ] item` and `- [x] item` as native interactive checkboxes.
- Persist across runs — Eleanore ticks boxes in Slack, and the canvas
  retains that state.
- Are re-readable via `slack_read_canvas`, which returns the current
  checked/unchecked state of every item.

**Benefit:** each run is a *diff* against the previous canvas — she never
re-sees an item she already handled.

## Workflow

### 0. Run-state tracking (in the canvas, not on local disk)

The skill performs **no local file writes**. Run state for catch-up
reporting (last successful run timestamp, recent run history) lives in
hidden marker comments at the top of the persistent canvas:

```
<!-- daily-slack-triage-canvas-id: F0B0D4JJMQQ -->
<!-- last-successful-run: 2026-04-27T17:08:00-07:00 -->
<!-- recent-runs: [{"ts":"2026-04-27T17:08-07:00","status":"success"},{"ts":"2026-04-26T17:08-07:00","status":"auth-failure","reason":"bridge_auth_unavailable"}] -->
```

Step 11 updates these markers after every run. Step 2.5 reads them for
catch-up. The `recent-runs` array is FIFO-trimmed to the last 10 entries.

### 0.5. Pre-flight auth + helper provision check (5-second budget)

Before doing any real work, verify the environment can actually reach
Slack. **Hard limit: 5 seconds total** — if anything hangs past that,
treat it as auth-failure and skip to step 11.

**Step 0.5a — confirm helpers are present:**

```bash
test -x /tmp/doordash-helpers-$(id -u)/linux-arm64/uv \
  && test -x /tmp/doordash-helpers-$(id -u)/linux-arm64/gh
```

If missing, attempt a single warm-up call to trigger bridge
provisioning: `gh --version` (provisions on demand). If still missing
after 5 seconds → `errors.push("helpers_not_provisioned")`, status
`auth-failure`, jump to step 11.

**Step 0.5b — confirm Slack auth is good without triggering browser:**

Run a lightweight `slack slack_read_user_profile` with a 5-second
timeout. Three outcomes:

- **Returns user data** → `auth_state.slack = "ok"`, proceed.
- **Returns "Bridge auth flow required" / "Login exited with code 2" /
  "requires authentication"** → `auth_state.slack = "needs_reauth"`,
  status `auth-failure`. **Do NOT wait for the browser to open in
  unattended mode.** Skip to step 11.
- **Times out** → `auth_state.slack = "unknown"`, status
  `auth-failure`, skip to step 11.

**Critical:** in unattended mode, never wait for browser auth. Fail
fast and log; the next interactive run will recover.

### 1. Load Slack CLI

Invoke `core:using-slack` before any Slack operation. The `slack` CLI
auto-provisions via the Cowork bridge; no manual auth. If a call stalls
with `[bridge] auth` in the output, tell Yi Jin:

> "A browser window should have opened on your Mac for authentication.
> Please complete the sign-in there."

### 2. Resolve identity and locate/create the triage canvas

Get her Slack user ID (`U02N4K114AK` is the known value — verify with
`slack_read_user_profile`). Store as `$USER_ID`.

Find the existing triage canvas:

1. Search her self-DM channel for a message that contains the persistent
   canvas link. A prior run records the canvas ID at the top of a marker
   message: `"<!-- daily-slack-triage-canvas-id: F123... -->"`.
2. If no canvas exists, go to step 7 and create one. Remember to record
   its ID so future runs find it.
3. Read the canvas with `slack_read_canvas` to get the current
   checked-state map. Build a set `CHECKED = { <permalink> | row.checked }`.

### 2.5. Catch-up reporting from previous failed runs

Read the `<!-- recent-runs: ... -->` marker from the existing canvas.
Find all entries since the last `status: success` run. If any
intermediate runs failed, build a catch-up summary like:

> ⚠️ 2 scheduled runs missed since last success:
> • 2026-04-25 17:08 PT — auth-failure (bridge_auth_unavailable)
> • 2026-04-26 17:08 PT — auth-failure (helpers_not_provisioned)

Prepend this summary to the canvas update for this run (above the
`## 📬 Daily Slack triage` heading) AND to the notification DM. Do
this BEFORE the regular workflow so Eleanore sees the gap even if
today's run finds zero unresolved items. Once surfaced, mark those
prior run entries with `"catch_up_surfaced": true` in the
`recent-runs` marker so they don't repeat on subsequent runs.

This widens the lookback window for THIS run only: when there are
missed runs, set `LOOKBACK = max(24h, time-since-last-successful-run)`
so threads that closed during the gap are still captured in the
decision log. Cap at 7 days as a safety bound.

### 3. Gather candidates from the last 24 hours

Compute the cutoff: `CUTOFF = now() - 24h`. Apply it to **every** source.

**Private channels are in scope.** Yi Jin has explicitly authorized private-
channel search for this skill; always use `slack_search_public_and_private`
with `channel_types="public_channel,private_channel,im,mpim"` rather than
`slack_search_public`. A thread in a private channel is still her work and
must not be silently dropped.

**Window filter uses latest activity, not thread opener.** For every
candidate, the in-window check is `max(message.ts for message in thread)
>= CUTOFF`, NOT `thread.opener.ts >= CUTOFF`. A thread that opened 30
hours ago but had a reply 4 hours ago is **in window**.

**a. @-mentions in public AND private channels**

```bash
slack slack_search_public_and_private \
  query="<@$USER_ID> after:$(date -d '1 day ago' +%Y-%m-%d)" \
  limit=20 sort=timestamp sort_dir=desc include_context=false \
  channel_types="public_channel,private_channel"
```

Paginate while `pagination_info` returns `cursor \`...\``. Parse the
markdown result: `### Result N of M` blocks with `Channel:`, `From:`,
`Time:`, `Message_ts:`, `Permalink:`, `Text:`. Dedupe by
`(channel_id, thread_ts)`.

**b. Threads she authored or posted in — `from:@me`**

**This pass is mandatory, not optional.** It catches the case where she
starts a thread (or joins one) without being @-mentioned by anyone — the
mention search misses these entirely.

```bash
slack slack_search_public_and_private \
  query="from:@me after:$(date -d '1 day ago' +%Y-%m-%d)" \
  limit=20 sort=timestamp sort_dir=desc include_context=false \
  channel_types="public_channel,private_channel"
```

For each result, resolve `(channel_id, thread_ts)` (use `Message_ts`
as `thread_ts` if the post is a top-level thread starter). Add the
thread to the candidate set if not already present via step (a). Step 4
then determines whether there's activity after her last message.

**c. DMs and group DMs — `to:me` search**

```bash
slack slack_search_public_and_private \
  query="to:me after:$(date -d '1 day ago' +%Y-%m-%d)" \
  limit=20 sort=timestamp sort_dir=desc include_context=false \
  channel_types="im,mpim"
```

This returns messages **to** her. **Do not rely on this list alone** to
decide who spoke last — search omits her own replies. Collect the set of
candidate DM channel IDs only; use step 4 to verify actual latest speaker.

### 4. Determine actual last-speaker from full channel history

**Critical step — do NOT skip.** For each candidate:

- **Channel threads:** call `slack_read_thread` with `response_format=concise`.
  Parse the thread into an ordered message list.
- **DMs / group DMs:** call `slack_read_channel` with `limit=50` to fetch
  the last ~1-2 days of messages. Parse the `=== Message from NAME (ID) ===`
  blocks; sort by `Message TS` descending.

For each candidate, find `latest_non_bot_speaker`:

- If `latest_non_bot_speaker.uid == $USER_ID` → **you replied, skip**.
- If someone else is the latest non-bot speaker → **candidate stays**.

Never infer who-spoke-last from search results alone — searches for
`to:me` or `<@$USER_ID>` exclude her outbound messages, so the comparison
is one-sided.

### 5. Drop resolved, noisy, and bot-filed items

Drop candidates matching any of these patterns:

**a. Explicit resolution keywords in the last 3 messages** (any author,
not just Eleanore): `fixed`, `resolved`, `closed`, `closing`, `back up`,
`works now`, `is working now`, `seemed to work`, `seems to work`,
`rolled back`, `reverted`, `redeployed .* fix`, `thanks for (fix|resolv|help|unblock|answer)`,
`all good`, `all set`, `unblocked`, `good to go`, `ship it`,
`:white_check_mark:`, `:heavy_check_mark:`, `:tada:`, `✅`, `🎉`.

**b. Handoff / routing closure** (last message from someone other than
Eleanore contains): `Adding <!subteam^`, `Adding <@`, `routing to`,
`escalating to`, `pinging .* team`, `assigning to`, `cc'?ing for visibility`,
`handed off to`, `.* will help`, `.* can help take a look`. This means
the reroute happened — no action needed from Eleanore.

**c. Conversation migration** (any recent message contains): `let's chat
in (the )?other thread`, `continuing in <https://`, `moved to #`,
`see <https://.*> for (the )?follow-up`, `started a thread here`. If the
target thread/DM is already in the candidate set, dedupe by keeping only
the target (the newer conversation location). Otherwise drop silently.

**d. Conversational closers in DMs** — drop when the other party's last
message is only one of: `^(sure|yes|yep|yeah|ok|okay|thanks|thx|thank you|
got it|sounds good|will do|cool|nice|:+1:|:thumbsup:|:white_check_mark:)\.?!?$`
or `^ok .{0,30}(thanks|confirm|good|great).*` (e.g., "ok got it, thanks
for confirming!", "ok sounds good!").

**e. Bot-filed requests from her awaiting others** — drop openers like
`New Request from <@$USER_ID>`, `New PR Review Request from: <@$USER_ID>`
that have no replies yet (she is waiting on others, not vice versa).

**f. Passive group `cc:` messages** where Eleanore is one of several
CCs with no direct ask — regex: `^\s*cc:?\s*(<@\w+>[\s,]*)+\s*(-|-{3})?\s*$`.

**g. Previously-checked items** — if `permalink in CHECKED`, skip.

**h. Broadcast / launch announcements** — openers formatted as broadcasts
with no direct question. Signals: leading `:rocket:` / `:tada:` /
`:megaphone:` emoji, phrases like `excited to (share|announce)`, `now in
(public|private) preview`, `now GA`, `launching`, `rolled out to`. If no
direct question is addressed to Eleanore in the thread, classify as P2 FYI
(do not drop entirely — she may still want awareness).

**i. Loosened conversational-closer detection.** In addition to the strict
`CLOSER_ONLY` / `CLOSER_COMPOUND` regexes, also drop DMs whose latest
message from the other party is **≤10 words** and ends with any of:
`thanks`, `thank you`, `good`, `got it`, `sounds good`, `no worries`,
`no problem`, `we are good to go`, `we're good`, `wink emoji`,
`smile emoji only`. Catches examples like "Oh sounds good. Thanks",
"sounds good thanks", "No worries :wink:", "put them in bags and we are
good to go".

### 6. Categorize and urgency-tag the survivors

**Categories** (first match wins, top to bottom):

1. **Pedregal launch blocker** — blockers for the Pedregal product launch;
   dependencies from Eradinus, Nexus, or other platform teams; signal
   words: `blocker`, `blocking launch`, `launch dependency`, or dependency
   team names.
2. **Reliability issue** — incidents, outages, latency, error rates, SLO
   burns, cost regressions, on-call pages.
3. **Pedregal feature gap / bug** — bug reports, feature requests, or
   functional issues tied to Pedregal. Channel name contains `pedregal` or
   the thread mentions Pedregal features/screens/flows.
4. **Support escalation** — threads from `#cx-*`, `#support-*`,
   `#eng-escalations`, `#help-*`, or asks tied to customer / merchant /
   Dasher-impacting issues.
5. **Other** — anything else.

Pedregal signal words (case-insensitive): `pedregal`, `eradinus`, `nexus`
(DoorDash platform, not the general word), Pedregal launch-milestone
references.

**Urgency (P0 / P1 / P2):**

- **P0 — Urgent.** Active incident language (`down`, `outage`,
  `customers impacted`, `blocking launch`, on-call pages, `urgent`,
  `ASAP`), direct asks from senior leaders, launch blockers flagged as
  critical, cost regressions ≥$5k/day or ≥+100%.
- **P1 — Needs response today.** Important stakeholder asking a direct
  question, unresolved blockers not yet critical, threads with 2+ follow-ups
  poking for a response.
- **P2 — FYI / low urgency.** Informational tags, non-urgent questions,
  asks with no deadline.

When ambiguous, prefer the higher urgency.

### 7. Build / update the canvas

Canvas title: `Daily Slack Triage — @eleanore.jin`
Canvas format (use mrkdwn-style checkboxes — Slack canvases render these
as native interactive checkboxes):

```markdown
<!-- daily-slack-triage-canvas-id: auto-filled by first-run post -->

## 📬 Daily Slack triage — last updated <YYYY-MM-DD HH:MM PT>

Items in the last 24 hours where the latest non-bot message is from someone
other than you. Tick items as you handle them; next run skips anything
you've checked.

### 🚨 P0 — Urgent (N)

- [ ] **[Pedregal launch blocker]** <one-sentence summary> — #<channel> — tagged by <display name> — <🆕 | ↩️> — <slack permalink>
- [ ] ...

### ⚠️ P1 — Needs response today (N)

- [ ] **[<category>]** ...

### ℹ️ P2 — FYI / low urgency (N)

- [ ] **[<category>]** ...

---

_Previous run: <timestamp>. <K> items carried over unchecked, <M> new._
```

Within each urgency tier, order items by category:
Pedregal launch blocker → Reliability issue → Pedregal feature gap / bug →
Support escalation → Other.

Per-item fields:

- Urgency + category tag in bold brackets.
- One-sentence summary ≤120 chars.
- Channel as `#channel-name` (not ID).
- Tagger as display name (not user ID).
- Permalink preserved verbatim — this is how she jumps into the thread.
- Status glyph: `🆕` no reply yet, `↩️` new follow-up since her reply.

**Carry-over logic:** unchecked items from the previous canvas stay if
they are still within the 1-day window and still unresolved; they are
moved to the top of their urgency section and marked with a trailing
` _(carried over from <prev date>)_` note. Items that fall out of the
1-day window are removed from the canvas, checked or not.

**If the canvas already exists:** use `slack_update_canvas` with
`action=replace` and the top-level section_id to rewrite the whole body.
**Preserve** the `<!-- daily-slack-triage-canvas-id: ... -->` comment at
the top.

**If creating for the first time:** use `slack_create_canvas` targeted at
her self-DM. After it returns `canvas_id`, post a message into her self-DM
with text `"Daily triage canvas created: <canvas_url>. I'll update this in
place every run."` so she has a permalink handy.

### 8. Post / update a short "new items" DM alongside

After the canvas update, also send a **single short message** to her
self-DM summarizing what's new this run:

> `📬 Triage updated — <N_new> new items, <N_carry> carried over. Canvas: <canvas_url>`

This gives her a Slack notification; the full detail lives in the canvas.

### 9. Empty-inbox case

If the final list is zero items: update the canvas to a single line
`✅ Inbox zero — no unresolved tagged items in the last 24 hours.`
and send the short DM: `✅ Triage — inbox zero.`

### 10. Post the daily decision log to Slack (Gmail fallback)

Capture every thread / DM that was **dropped as closed** during steps 4-5
(keyword closures, handoff / routing, conversation migration, Eleanore was
last speaker, DM conversational resolution) and post the assembled log
**directly to her Slack self-DM** as a separate message after the triage
notification. Eleanore archives it to her own knowledge base manually —
the skill does NOT write to local disk.

**Selection rules:**

- Skip DM entries that resolved via conversational closers only ("Sure",
  "ok got it, thanks", "yeah", etc.) — they carry no decision content.
- Skip passive group `cc:` mentions — no decision captured.
- Include substantive closures even when Eleanore was the last speaker
  (she may have been the one who gave the answer / made the call).

**Content format (markdown, posted in a single Slack message):**

```markdown
📒 Daily Slack Decision Log — <YYYY-MM-DD>

<one-line run summary: N threads, M DMs captured>

## <channel-or-dm-name> — <short thread topic>

- **Link:** <slack permalink>
- **Problem:** <1-3 sentences: what was being asked, what was stuck, what
  triggered the thread>
- **Decision / Conclusion:** <1-3 sentences: what was resolved, what was
  agreed, what was routed/handed off, or what workaround landed>
- **Decision makers:** <comma-separated display names of people who drove
  the decision — whoever made calls, routed, or confirmed resolution;
  typically 1-4 names; include Eleanore when she made the call>
- **Closure type:** <keyword-closure | handoff | conversation-migration |
  she-was-last-speaker | dm-resolved>

## <next entry>
...
```

**How to fill each field:**

- **Problem:** synthesize from the thread opener and the first few
  replies. Do not just copy the opener verbatim — summarize.
- **Decision / Conclusion:** synthesize from the last 2-5 messages.
  Examples: "Routed to pretzel-core subteam for review", "Rolled back
  deployment to 1.1565.0, confirmed fixed", "Confirmed we can only
  ingest Cassandra → Snowflake via pepto, not datalake".
- **Decision makers:** the people whose messages drove the closure. For
  a routing closure, the person who did the routing. For a keyword
  closure, whoever confirmed the fix. For a technical decision, whoever
  made the call. Include Eleanore when she made the call. Use display
  names, not user IDs.
- **Closure type:** one of `keyword-closure`, `handoff`,
  `conversation-migration`, `she-was-last-speaker`, `dm-resolved`.

**Ordering:** group by channel (or "Direct Messages" for DMs), then
chronological by first thread message.

**Delivery — Slack primary, Gmail fallback:**

1. **Slack DM (primary).** Send the full decision log content as a
   single Slack DM to her self-DM via `slack_send_message` with
   `channel_id = $USER_ID`. If the content exceeds ~35,000 chars (Slack's
   hard limit is 40k), split across sequential messages numbered
   `(1/N)`, `(2/N)`, etc. — preserve full content.

2. **Gmail email (fallback).** If the Slack post fails — auth error,
   network error, rate-limited, anything — send the full decision log
   content via Gmail to yi.jin@doordash.com. Use `gws gmail send` (or
   equivalent `send-gmail-message` skill). Format:

   ```
   To: yi.jin@doordash.com
   Subject: 📒 Daily Slack decision log — <YYYY-MM-DD>
   Body: <full decision log markdown>
   ```

   Gmail handles long content gracefully (no need to split).

**If both Slack and Gmail fail:** include the decision log as a
collapsed quote inside the auth-failure email (step 11) — the user
gets it via the same email that tells them auth is broken.

**No content is ever written to local disk.** Eleanore copies the log
content from Slack (or Gmail) to her local knowledge base
(`/Users/yi.jin/Projects/eleanore-knowledge-base/raw/slack-messages/`)
manually on her own schedule.

**Empty decision log case:** if zero threads closed in-window, skip
this step entirely (don't post an empty log message).

### 11. Always finalize the run state in the canvas markers

This step runs **on every code path** — success, no-data, auth-failure,
partial-failure, error. Never skip it.

**Update the canvas marker comments** at the top of the persistent
canvas via `slack_update_canvas`:

- `<!-- last-successful-run: <ISO timestamp> -->` — only update on
  success or no-data outcomes; leave previous value on failures so
  catch-up reporting still finds the right baseline.
- `<!-- recent-runs: [...] -->` — append this run's entry as
  `{"ts": "<ISO>", "status": "<outcome>", "reason": "<error key>"}`,
  trim to the last 10 entries (FIFO).

If the canvas itself is unreachable (Slack auth fully broken), skip
the marker update — the email fallback in this step will surface the
failure regardless.

**Auth-failure path — Slack-DM is unusable, so use Gmail:**

When `status == "auth-failure"`:

1. Skip the Slack triage notification and Slack decision log post —
   they're impossible.
2. Send a single Gmail email to yi.jin@doordash.com:

   ```
   To: yi.jin@doordash.com
   Subject: ⚠️ Daily Slack triage skipped — <reason> at <time>
   Body:
     Hi Eleanore,

     Your scheduled daily Slack triage at <fired_at> couldn't run.

     Reason: <human-readable failure reason>
     Last successful run: <timestamp> (<N> runs missed since then)

     Recovery: open Cowork on your Mac and run any Slack-touching skill
     (e.g. "summarize my slack mentions"). That refreshes the Slack
     auth tokens. The next scheduled run will then replay the missed
     window automatically.

     — daily-slack-triage skill (auto-generated)
   ```

3. **Inbox-spam control:** before sending, read the canvas
   `<!-- recent-runs: ... -->` marker (if reachable) — if the
   immediately-prior run was also `auth-failure` with the same reason,
   skip the email. Send only on the first failure in a consecutive
   streak. If the canvas isn't reachable, send the email anyway
   (better one extra email than silence).

4. If Gmail also fails (rare — `gws` auth is independent of Slack),
   create a Google Calendar event on her primary calendar titled
   `⚠️ Slack triage skipped — reauth needed` for the current 30-minute
   slot as a last-resort signal.

The skill itself does NOT try to send Slack DMs about Slack-auth
failures (chicken-and-egg). All recovery state lives either in the
canvas markers (when canvas is reachable) or implicitly in Gmail
(when not).

## Constraints

- **1-day window is strict** — it applies to every category and every
  priority tier. A P0 from 26 hours ago does not enter the digest.
- **Never post outside her self-DM.** No replies, reactions, or messages
  in source threads.
- **Never skip step 4** — last-speaker determination must come from full
  channel history, not search results.
- **Always include private channels** in the mention search — the user has
  authorized this. Never fall back to `slack_search_public`-only for
  mentions.
- **Always run the `from:@me` pass** — threads Eleanore started or posted
  in without being @-tagged back are not covered by mention search.
- **Window filter uses latest-activity timestamp**, not opener timestamp —
  a long-running thread with a recent reply must stay in scope.
- **Preserve permalinks verbatim.**
- **Reuse the canvas across runs** — never create a second canvas.
- **Categorization is best-guess** — prefer the more urgent category when
  ambiguous (launch blocker > reliability > bug > support > other).
- **No local file writes — ever.** Run state lives in the canvas
  markers, decision logs go to Slack DM (Gmail fallback). Eleanore
  archives content to her own knowledge base manually. The skill
  never touches `/Users/yi.jin/...` paths.
- **Decision log idempotency by permalink** — if re-running on the same
  day, the in-memory dedup uses canvas state plus the most recent
  decision-log Slack DM to skip already-posted entries. Best-effort,
  not strictly enforced.
- **Never wait for browser auth in unattended mode.** The pre-flight
  check has a hard 5-second budget; if Slack auth isn't already cached,
  fail fast. The bridge's interactive auth flow is for interactive
  sessions only.
- **Always finalize step 11**, even on early-exit paths (auth-failure,
  no-data, error). Canvas marker update + email fallback are
  non-skippable.
- **Auth-failure recovery is deferred to the next interactive
  session.** Email fallback notifies Eleanore; she opens Cowork, uses
  any Slack-touching skill to refresh tokens, and the next scheduled
  run replays the gap.
- **Failure notifications: Slack DM → Gmail → Calendar event.** No
  local sentinel. Email rate-limited to once per consecutive
  same-reason failure streak.

## Error handling

- Slack search returns empty across all sources → still update the canvas
  to the ✅ inbox-zero state and send the short DM.
- Canvas not found mid-run (was deleted) → create a new one, update its
  ID marker.
- Canvas update fails → fall back to posting the full digest as a regular
  message in her self-DM and flag the fallback explicitly.
- `slack_read_canvas` returns no items but the canvas exists → treat as
  empty checked-set (fresh canvas).

## Related skills

- `summarize-slack-thread` — deep-dive on a single flagged thread.
- `pedregal-biweekly-status` — 2-week Pedregal Data Platform doc.
- `pedregal-mob-weekly-update` — weekly MOB tracker.
