// NOT PINE CODE — this is a markdown guide. Do not paste it into the Pine Editor.
// The script it documents is: tools/cisd-ultimate-balanced.pine  (that file is the code).
// For the v2 line (gates, funnel, journal) see tools/archive/cisd-v2-guide.md.

# CISD Ultimate v1 — the iFVG / open-time build

`cisd-ultimate-balanced.pine` is the script that was pasted into this project at the start. It was
the audit baseline for a round, and it is now the working file again, with the machinery its iFVG
and time-of-day story always needed. v2 and the overlay are set aside, not deleted.

Pristine copy of the file as it arrived (before these edits): `tools/archive/cisd-ultimate-balanced.pristine-v1.pine`.
It is dot-prefixed so nobody pastes it by accident; it exists so any decision below can be reversed.

## 1. What changed, and why each piece is behind a switch

Nine defects were found by reading the file end to end (the full record is `tools/cisd-audit.md` §13).
Every one that touches *what the script means* is fixed unconditionally, because a switch that
defaults to "wrong" is a trap; everything that adds *behaviour* is opt-in:

| what | switch | default |
|---|---|---|
| iFVG polarity + zone (it drew the opposite side's gap, in the opposite colour) | — | fixed |
| iFVG registry (was: one object ever, never invalidated) | `iFVG layer` | `Track only` |
| iFVG entries: tap the level, close rejecting, one entry per zone | `iFVG layer` | `Track only` → no entries at all |
| entries counted in the score | `iFVG layer` = `Track + score` | off |
| entries required before signalling | `iFVG layer` = `Track + score + gate` | off |
| entry level inside the zone | `Entry level in the inverted zone` | CE (50 %) |
| how decisive the break must be | `Invalidation needs a body of (ATR ×)` | 0.80 |
| minute-accurate windows, 5 killzones, SB hours, 5 macro cores | `Trading window` | `Killzone` |
| public vs 2017 killzone set | `Killzone set` | Public 2022 |
| London close + NY PM windows | their own booleans | off |
| no new signals after hour N | `No new signals after this NY hour` | 16 (off) |
| that cutoff, applied to iFVG entries too (the gate read `(not clockOk or true)`, a term that cannot fail) | `Apply the after-hours cutoff to inverted entries` | **on** - behaviour change, one toggle from off |
| target = the session that FINISHED, not the one still printing | `Target the finished session's extreme` | **on** - moves the drawn target; the live accumulator includes the current bar |
| the reference candle re-rolls inside the day (the hourly-anchor reading) | `Anchor cadence` | `Once per day` - opt-in, §6 |
| NY AM opening range as a pool | `Use the 08:00 opening range as a pool` | off |
| entries gated on an opening-range sweep | `Require an opening-range sweep` | off |
| strict sweep (wick through **and** close back inside) | `Sweep = wick through AND close back inside` | **on** |
| minimum wick share of the candle | `Min wick as share of the candle range` | 0.60 |
| repaired displacement ratio (audit §1a) | `Strict displacement ratio` | off |
| score composition: displacement / premium-discount / body % / iFVG | `Score composition` group | disp on, others off |
| spent levels kept visible but bounded (was: leaked forever) | `Keep up to N spent levels visible` | 24 |
| per-side zone cooldown (was: one shared 3-bar counter) | `Bars between new zones (per side)` | 1 |
| painted-candle overlay | `Overlay painted candles in the trend colour` | on |
| session extremes and the prior day's bounds as raidable levels | `Track each session's high and low as a level` | off - §8 |
| which sessions are pooled, and whether PDH/PDL join them | five per-session booleans + `Add the prior day's high and low` | Asia / London / NY AM on, London close / NY PM off, PDH/PDL on |
| how a level dies, and how long it waits | `A level is taken when` / `Projection` | `Close through` / `Until taken` |

Fixed with no switch, because they were simply wrong: the pivot detector now runs on `high`/`low`
instead of the default `hlc3` while the level drawn was `high[len]`/`low[len]`; the entry marks are
tracked and retired instead of orphaned; the `iFVG ACTIVE` panel row counts live zones; the alert
message now carries entry/SL/TP/body %/window.

## 2. Recipe: iFVGs at the open, gold or index futures, 5m

```
Timeframe preset          5min
Trading window            Killzone
London open               on        New York AM         on
Mark the Silver Bullet    on        Mark the five macro cores   on
No new signals after      11          (strict NY AM read; 16 = all day)
Use the 08:00 opening range         on     Range length 30     Sweep window 09 → 11
Require an opening-range sweep      on     ← this is the actual filter
iFVG layer                Track + score + gate
Entry level               CE (50 %)       Invalidation body 0.80 ATR
Live inverted zones       2 per side      Inverted zone expiry 180
Show Live FVGs / iFVGs    on              Bars between new zones 1
Sweep strict              on              Score min for BEST 2
```
Why those: `11-silver-bullet/silver-bullet-rules.md` makes the window item 1 of 8 and non-negotiable,
`31-models/ny-am-open-range-model.md` makes the opening range the pool that gets raided in
09:00–11:00, and `02-liquidity/liquidity-sweep.md` is why a touch of a level is not a sweep. What is
left for you is the judgement the script cannot make: whether the HTF day is *for* that direction.

Quieter / afternoon variant: `Trading window = Killzone + Macro`, `London close` + `New York PM` on,
`Use the 08:00 opening range` off, `No new signals after` 16.

## 3. Reading the panel

Rows 0–12, one line each: `Score` (now `n/m`, m = what is actually being scored), `Analysis`
(which zones are live), `Live FVGs`, `Live OBs`, `iFVG` (`2 inverted / 8 gaps` — gaps are the memory
the inversions are computed from), `Prem/Disc`, `HTF Bias`, `Window` (what you filtered on, plus
`+SB` / `+MACRO` when you are inside one), `Ready`, `Preset`, `Open range` (its two levels and which
bound has been taken), `Score parts` (so the grade is auditable at a glance), `iFVG tap` (the entry
level if a zone was tapped on this bar).

## 4. Cost, measured

`python3 tools/pine-gate-run.py tools/cisd-ultimate-balanced.pine` at 1200 bars, best of 3, runtime's
own `elapsed_ms`: **553 ms**, against **390 ms** for the file as it arrived. The new figure is an
upper bound, not a fair one: to make the iFVG code paths execute at all the harness injects a
synthetic gap on nearly every bar and lets `ifvgDisp` fall to 0, so the engine is running far harder
than it will on a real chart where `fvTop` is capped at 8 and gaps are not printed every bar. The
object counts are also capped by construction now: ≤ 2 inverted zones per side, ≤ 12 entry labels,
≤ 36 entry lines, ≤ 24 spent levels per side.

Verification that ran on this revision: pine-lint (TV-parity type checker) clean ·
`tools/pine-validate.py` 0 findings with `--selftest` PASS · `pyne check` OK · `pyne run` 1200 bars,
gap memory at its cap, inverted zones created and deleted without error. None of that certifies the
*signals* — see `tools/cisd-audit.md` §9d for what the reference runtime cannot tell you.

## 5. The 4H candle-range layer (`grp_crt`) — added 2026-10-10, off by default

This is the screenshot phase's build: the reference-candle model in `tools/crt-candle-range-study.md`
(the 4H-candle range, the 01:30 NY raid, the daily OHLC ladder, the stand-aside list). **27 switches, and
the layer does nothing until you switch `Use a reference candle's range as the day's grid` on** — including
`crtGateCore` and `scCrt`, the only two hooks into the CISD core, both off, so your existing signals and
scores are bit-for-bit what they were. The daily ladder was folded into the `"D"` call the file already
made, so this layer costs **no additional `request.security`** (still 3 total).

### The recipe for the 01:30 raid, which is what the screenshots describe

1. Chart: EURUSD or GBPUSD, **15m or 1h**, and your clock must be New York (`GMT-4`/`GMT-5`). The
   reference is built from the NY clock inside the script, so a 17:00-anchored template and a
   00:00-anchored one agree — but the *hour you type in* is only meaningful if the timezone setting is
   New York. Check it once; `17:00` labels on your 4H candles are the tell that it is.
2. `Reference range` = **Prev 4H candle**. This is candle 1 of the classic definition. At 01:30 the
   01:00 candle's bounds are not finished, so the thing being raided is the candle that *ended* at 01:00.
3. `Anchor candle opens at this NY hour` = **1**, `window opens N min after` = **0**,
   `length` = **90**. Their printed example is a sweep at 01:30 = 30 minutes in; 90 keeps the whole
   first hour and a half. `No raid inside the window = no setup` stays on — that rule is the model's
   own ("Time Condition > Price Condition").
4. `Direction filter` = **HTF bias** (their checklist's step 1 is "daily bias or stop"),
   `Entry trigger` = **Anchor open retest** (the "4H Key" in their panels *is* the anchor open),
   `Target` = **Opposite bound**, `Stop` = **Sweep extreme**.
5. Leave `Apply the 2017 stand-aside list` **on**. It is the failure catalogue: prior-day range over
   2× the 5-day ADR, CBDR over 50 pips, Asian range over 40 pips, a move already running from 20:00
   NY, no overnight consolidation, three consecutive daily closes against the direction. When one of
   them is true the panel says which one and the layer stays quiet — that is the whole point of it.
6. For iFVG-at-the-open work, set `Entry trigger` = **iFVG tap** instead of step 4's retest: the raid
   arms the setup and the inverted zone is where you take it. That is the one element of their model
   this file already had machinery for.

### What the two new panel rows mean

`4H CRT` is the state and the three levels: `watching the bounds`, `armed — waiting for the trigger`,
`live`, `delivered`, `stopped`, `void`, or `STAND ASIDE: <which condition>`. `CRT why` is the last thing
that happened plus the running record — `W/L/be/void` counts, net R, the win rate off entries taken, and
**the average R that was available at the opposite bound**, which is the number that tells you whether
the "+3RR" label in those posts is real on your pair (on the prices printed in the screenshot it is
about 2.2R, and the community ladder of 50%-then-bound lands 1.6–2.8R, which is what the box measures).

### Alerts

Four conditions, so the failures are alertable too: `CRT bound raided and accepted back`, `CRT entry`,
`CRT outcome (target or stop)`, `CRT void / abandoned`. If you want the stand-aside day as an alert,
alert on the void condition and read the panel: the raid that never happens and the day that was never
tradeable both end there.

### Deliberately not built

* **Weekly market profile** — Pine has no TPO/profile object. A bar-count "value area" wearing that
  name would be the one thing on the panel that teaches you something false; use TradingView's Volume
  Profile instead.
* **`Model 1` as a name** — it is @MadoCRT's course material (C³, launched 2026-10-15), never defined
  publicly. The rules the charts actually show are implemented and named for what they do.
* **SMT divergence** — needs the sibling symbol on your plan. The working module is in
  `tools/archive/mx-context-overlay.pine` and can be lifted in one pass if you have the data.
* **Three of ICT's eight stand-aside conditions** (a named holiday, an unscheduled driver, the count of
  scheduled events) need an economic calendar Pine cannot read. The first-Friday proxy for NFP defaults
  to *Mark only* rather than blocking, because a date rule is not a calendar.

### Cost

Three switches arrived after the first build, all of them about the C1/C2/C3 sequence:
`Reference candle length (min)` (240 for the 4H anchor, **60 for the hourly anchors the library lists**
— 02:00 / 03:00 / 05:00 / 09:00 / 13:00 NY — which the first build could not express),
`Acceptance is C2's own close (textbook C1/C2)` (off: the shipped default judges the acceptance on any
bar inside the window, which is what the screenshots show — they entered at 01:30, hours before C2
closed; on: the raid is remembered, the stop sits behind its deepest tap, and the test settles only at
C2's close), and `Enter only inside C3` (off: on, an armed setup may not be entered until C2 has
closed, so the trigger is a retest in the delivery candle).

Measured on the current harness with the layer off — the shipped default — the file runs at
**670–730 ms** at 1200 bars, best of 3, with a run-to-run spread of about ±60 ms. Two things worth
saying about that number rather than dressing it up: the **567 ms** recorded in audit §13 is not a
clean control (this harness has since grown eight probes and three exercise builds), and an earlier
draft of this section claimed a 14× speed-up from moving the 2017 gates to once a day — that was
**Numba compile cost in a single-repetition run, not the script**, and the claim is retracted. The
daily-scoping was kept anyway, because it is what the source prescribes ("checked at midnight NY") and
it fixed a real bug: on a chart shorter than one session the stand-aside list had never been evaluated.

What the harness can certify here ends at the clock. The time gates cannot be exercised at all — pyne
runs 1-day synthetic bars whose clock barely moves — so `Reference candle opens at this NY hour`,
the sweep window and the delivery expiry are verified statically and need one look on a real chart at
01:00 NY.

## 6. Switching timeframes (added 2026-10-10)

`Timeframe Preset` defaults to **`Auto from chart`** now. It reads `timeframe.in_seconds()`, selects the
matching tier of the ladder (`<=180s 3min`, `<=300 5min`, `<=900 15min`, `<=1800 30min`, `<=3900 60min`,
`<=15000 240min`, else `1D`), and rescales the bar-count parameters so they keep their **duration** instead
of their bar count: expiry, the liquidity lookback, the stale-BEST window, the iFVG age, the CRT
order-block age, and three windows that used to be literals in the code (FVG freshness 10, order-block
freshness 12, premium/discount range 25).

Three things to hold on to:

* On a 5m chart the new default is a **no-op**: the scale is exactly 1 and every derived window lands on
  the number the inputs already carried. Nothing about the signals changed for the chart the file was
  tuned on, which is what made it safe to re-default.
* **1m / 2m / 3m charts do change, and that is the fix, not the feature.** The ladder's first rung had been
  renamed to `if tier == "%s"` - a placeholder that matches nothing - so a 3-minute chart selected the `3min`
  tier, printed it on the panel, and applied the input values instead (0.55 / len 8 / cooldown 5 / 0.40 /
  2.5 were unreachable). Audit §16 has the attribution; `pine-validate.py` now refuses the class, against a
  control file that is the real defect rather than a fixture.
* It **selects a tier, it does not interpolate**. The ladder is hand-tuned per timeframe by the source
  material and is not linear in time, so a 20m chart gets the `30min` tier rather than an invented average.
  `60min`, `240min` and `1D` are my extrapolation of the trend, not tuning from a source, and nothing at
  1H+ is backtested. The panel's first row prints the tier and the scale, and both BEST alerts print the
  tier, so the assumption is visible instead of load-bearing.
* A named tier overrides the ladder **without** unscaling the windows; `Custom` is the only way to pin them
  to the numbers you typed. Those are two separate knobs on purpose.

What still does not adapt, and cannot: `HTF for Bias` (see its tooltip - `request.security` wants a constant
timeframe, so a computed one risks the whole script failing to paste), the two pip-denominated caps, the
session you pick, and your key levels. `tools/settings-by-pair.md` is the maintained matrix for all of that,
including the generated table below and the per-pair substitutions for gold and the index CFDs.

```
| chart | tier it picks | scale | expiry | liq look | clean after | iFVG age | CRT / OB age | FVG / OB fresh | prem-disc | expiry as time | clean as time |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1m | `3min` | x5 | 300 | 60 | 175 | 900 | 60 | 50 / 60 | 125 | 5.0 h | 2.9 h |
| 3m | `3min` | x1.67 | 100 | 20 | 58 | 300 | 20 | 17 / 20 | 42 | 5.0 h | 2.9 h |
| 5m | `5min` | x1 | 60 | 12 | 35 | 180 | 12 | 10 / 12 | 25 | 5.0 h | 2.9 h |
| 15m | `15min` | x0.3333 | 20 | 4 | 12 | 60 | 4 | 3 / 4 | 8 | 5.0 h | 3.0 h |
| 30m | `30min` | x0.1667 | 10 | 3 | 6 | 30 | 3 | 3 / 3 | 8 | 5.0 h | 3.0 h |
| 60m | `60min` | x0.0833 | 5 | 3 | 3 | 15 | 3 | 3 / 3 | 8 | 5.0 h | 3.0 h |
| 4H | `240min` | x0.0208 | 3 | 3 | 3 | 4 | 3 | 3 / 3 | 8 | 12.0 h | 12.0 h |
| 1D | `1D` | x0.0035 | 3 | 3 | 3 | 3 | 3 | 3 / 3 | 8 | 72 h | 72 h |
```

Generated by `python3 tools/tf-scale-table.py`, which mirrors the shipped formula; the last two columns are
the reason to trust the middle ones, and the 4H/1D rows are the reason to stay sceptical above 1H.

## 7. Install on TradingView, step by step

1. **Copy the code, never the docs.** The file is `tools/cisd-ultimate-balanced.pine`. Locally:
   `pbcopy < tools/cisd-ultimate-balanced.pine` (macOS) or `xclip -selection clipboard < ...` (Linux); from
   GitHub, open the file on the session branch, press Raw, select all. After pasting, line 1 must still read
   `//@version=6`. A `.md` pasted instead produces a misleading "unspecified Pine version" error, which is why
   every doc in this folder opens with a `//` line saying it is not code.
2. **Delete the old instance before adding the new one.** Chart legend, hover `CISD Ult`, click ×. TV caches
   the compiled build per script name, so a stale instance is the single most common reason "I changed it and
   nothing happened".
3. **Paste and add.** Chart → bottom panel → Pine Editor → New Script → replace everything → Save As
   `CISD Ultimate Balanced` → Add to chart.
4. **Confirm the build.** The legend must read **`CISD Ultimate Balanced · build 2026-10-13-killzone`**.
   The tag is bumped whenever the file changes, so this step is a fact and not a guess; if the legend shows the old string you are looking at
   the old compile, and nothing you conclude from that chart is about this file.
5. **Choose the chart.** `EURUSD` or `GBPUSD`, 5m or 15m, is what everything here is tuned and verified for.
   Time-based chart types only: on Renko / Range / Line Break / Kagi there is no bar duration, so the auto
   tier falls back to the `5min` ladder with no rescaling - it will not error, and it will not adapt either.
   **Your chart timezone is irrelevant on purpose.** Every clock test is `hour(time, "America/New_York")` in
   the code (see the two `ny_hour`/`nyMin` blocks), so 01:00 means 01:00 New York whatever your account
   settings say. There is no timezone option to find, and "the panel is wrong because my TV is set to Paris"
   is not a thing that can happen here.
6. **Read the first panel row.** It should say `5min / 5 x1` on a 5-minute chart, `15min / 15 x0.3333` on a
   15-minute one. That row is the auto-tier feature: it tells you which ladder you got and whether the windows
   were rescaled, so you never have to remember what you set. `windows as written` means `preset = Custom`,
   `no bar duration here` means a chart type with no timeframe.
7. **Switches for the A+ open-based playbook** (the use case this build was pointed at):

   | switch | set to | note |
   |---|---|---|
   | `Timeframe Preset` | `Auto from chart` | leave it |
   | `Require Liquidity Sweep`, `Require FVG / iFVG`, `Require Strong Displacement` | on | the three the model treats as the entry condition |
   | `Minimum Score for BEST` | 3 | 2 is the shipped default; 3 is the "only A+ / premium setups" setting |
   | `iFVG layer` | `Track + score` | `Track + score + gate` refuses entries outside the window as well |
   | `Inverted zone expiry (bars)` | leave | auto-scaled; 60 bars on 15m, the same 15 hours |
   | `Use a reference candle's range as the box` (`crtOn`) | **on** | off by default because it is a second model |
   | `Reference candle length (min)` | 240 | the 4H candle that opens at `crtAnchorH` 01:00 NY |
   | `Acceptance` / `Direction filter` | `Close back inside` / `HTF bias` | shipped defaults, and the two things the sources say not to negotiate |
   | `Apply the 2017 stand-aside list` | on | shipped default; the panel says why it stood aside |
   | `HTF for Bias` | `60` on 5m/15m | the one input the script will not derive: see its tooltip |
| `Track each session's high and low as a level` (`kzlOn`) | on, if you watch the session levels | off by default - a second model again, and a draw-and-count one (§8). It cannot change a CISD signal |
8. **Alerts come in two kinds, and the difference bites.** Under the indicator's ⚙ / Create Alert:
   * the twelve **conditions** (`BEST Bearish CISD`, `BEST Bullish CISD`, `iFVG Inversion Long`/`Short`,
     `NY opening range high swept`/`low swept`, `CRT bound raided and accepted back`, `CRT entry`,
     `CRT outcome (target or stop)`, `CRT void / abandoned`, `KZL level raided and rejected`, `KZL level taken`) - pick the named condition, **Once Per bar Close**;
   * the five **messages** built at runtime (`iFVG ...`, `CRT long ...`, `KZL ASIA high ...`, `BEST BEARISH ...`, `BEST BULLISH ...`)
     carry the entry, SL, TP, pips and the tier in the text. Those need Condition =
     **Any alert() function call**, which is the one to pick if you want the numbers in the notification.
   The opening-range pair only exists with `useOR` on, the four CRT ones with `crtOn` and the two KZL ones with `kzlOn`: their
   conditions are `useOR and ...` / `crtOn and ...` / `kzlOn and ...` in the code, so a silent alert is usually a switch, not a bug.
9. **Change the timeframe and check one thing.** Row 1 should change by itself and the signals should keep
   their meaning. If `15m / 15 x1` ever appears, the scaling did not engage - that is a bug, not tuning.
10. **Next session:** watch 01:00-02:30 NY once with `crtDraw` on and confirm the reference box, the raid
    marker and the sweep-window row line up with the clock. That is the one part of this file the harness
    cannot exercise (pyne runs 1-day synthetic bars, so the minute gates never open), and it is the only
    verification step left that requires your eyes.
11. **If drawings go missing** on a lower TradingView plan: the script asks for 500 lines / 500 labels /
    80 boxes. Lower `Max FVGs per side`, `Max OBs per side`, `Live inverted zones per side` and
    `Keep up to N spent levels visible` (24) - the objects, not the logic. The killzone level layer does not need asking: `Live levels kept` caps
    it at 12 lines and 12 labels whatever your timeframe, which is exactly why its levels are projected with
    `extend.right` rather than re-stamped at the right edge. Nothing in the signal path depends
    on how many are drawn, except the zones-near-price filter.

## 8. The killzone level layer (`grp_kzl`) — added 2026-10-13, off by default

The picture that started it was a 15m NQ chart where yesterday's Asian high was still a horizontal line this
morning. That is not decoration: an un-raided session extreme is resting orders nobody has filled yet, and
the sentence every source uses for a tradeable day - "Daily Bias → DOL → Key Levels → 4H CRT → LTF
confirmation" - has *key levels* in it as a step, not as a vibe. The inventory, the object budget and the
extend-vs-new verdict are `tools/mx-setups-study.md` §8. What shipped is P1, the **draw-and-count** half.

**No score, no gate and no entry consults these levels.** Lines, states, two panel rows, two alerts, one
message. Feeding them into the CISD score is P2 and it is a decision this build does not make, because it
would move signals on charts that only wanted the drawing.

### What it draws

* when a pooled session **ends**, its high and its low are pushed onto a level registry - Asia, London,
  NY AM, London close, NY PM, plus `PDH`/`PDL` if `Add the prior day's high and low` is on. A session has
  to have spanned `A session must span at least this many bars` or nothing is created, which is also what
  stops a thin index CFD feed that never prints London from inventing a London range.
* each level is an `extend.right` line with one small label at the session edge (`ASIA High`, `NYAM Low`).
  The label is placed once and never moved, and a live level costs **zero** object calls per bar - which is
  the only reason a 500-line budget can carry days of levels at once.
* three states, because the distinction is the whole information: **live** (solid), **raided and held**
  (dashed and thicker: price took out the level and closed back inside, the sweep the model wants),
  **taken** (dotted and grey, the line cut off at the bar that closed through it, no longer projected).
* while a session is still forming its window is shaded with `bgcolor`. Painted spans, not boxes, on
  purpose: `max_boxes_count` is 80 and is shared with the FVG and order-block registries, where box
  starvation has already been an audited failure of this file.

### The switches

| label | default | what it decides |
|---|---|---|
| `Track each session's high and low as a level` | **off** | the layer. Off, the panel reads `layer off` on both rows and nothing else here runs |
| `Asia levels (20:00-00:00 NY)`, `London levels`, `New York AM levels` | on | the three sessions whose extremes carry information in the playbook this file is tuned for |
| `London close levels`, `New York PM levels` | off | two-hour windows; 3 bars on a 30m chart, 7-8 on 15m |
| `Add the prior day's high and low` | on | free: `pd_high`/`pd_low` already come back on the daily `request.security` tuple the 2017 stand-aside list uses. On CME feeds "prior day" is the **Globex** day, not midnight to midnight - the tooltip says so, because a line that lands on the wrong session is otherwise read as a bug |
| `Projection` | `Until taken` | `Today only` and `3 days` retire by session count instead; `Until taken` is the reference behaviour, an unmitigated high is still a draw two days later |
| `A level is taken when` | `Close through` | the same sweep arithmetic used everywhere else in this file (a sweep wicks, BOS closes). `Wick through` retires a level the first time it is poked, which is the other school |
| `A session must span at least this many bars` | 6 | scaled by the auto tier like every other bar count - what that means for your timeframe is the last column of `tools/settings-by-pair.md` §2 |
| `Live levels kept` | 12 | five sessions × two bounds × a day and a half is ten; past the cap the oldest are dropped, so the count is bounded on any timeframe |
| `Name each level at its session edge` | on | off removes the labels, not the levels |
| `Shade the session that is forming` | on | the `bgcolor` |

### Panel and alerts

`KZL levels` reads `N live / M made / R raided / T taken` for the life of the chart, and `KZL last` names
the most recent event (`LNDN high 1.1742 raided, closed back inside`). The conditions are `KZL level raided
and rejected` and `KZL level taken`; the runtime message is one `alert()` in the shape of
`KZL ASIA low 20815.0 closed through | 9 live | NQ 15 | 15min`, which is what the "Any alert() function
call" recipe in §7 picks up. Raid and take are counted separately on purpose: a day that is all takes is a
day where the levels are run through, and a day that is all raids is a day where every poke at liquidity
fails - those are not the same trading day, and they are not the same next trade.

### Three things this deliberately is not

1. **Not the five `kz_*` gate switches.** The plan was to reuse them. Reading the two against each other
   changed that: `kz_asia` off means "do not signal in Asia", not "the Asian range is irrelevant", which is
   precisely what someone trading London needs the Asian high for. An information layer should not be
   hostage to a gate switch.
2. **Not the same "Asia" as the targets.** The pooled window is 20:00-00:00 NY - the same block `wAsiaKz`
   gates on and the same window the 2017 list measures - while the *target* preference list uses this file's
   18:00-02:00 Asian accumulator. Both exist, both are labelled; silently unifying them would be a change
   nobody asked for.
3. **Not a setup model.** There is no "Asian high raided + short bias ⇒ entry" here. That is P2, and it
   earns its place by measurement, not because the lines are now drawn.

### Cost, and what has not been verified

158 lines, 13 inputs, 13 `var` arrays and 4 scalars, 6 functions, **no new `request.security` call, no new
plot, no new box**, and zero object calls per bar for a level that nobody has touched. The reference
runtime runs it green twice over: with the shipped defaults on synthetic daily bars (every counter zero,
which is the *correct* answer when the clock never enters a session) and as the gate's sixth exercise, where
1198 levels are made, 599 are taken, 599 are raided and held, and the registry sits at exactly the 12-level
cap. Creation, projection, both transitions, day-staleness and the cap are therefore executed code, not
compiled text. What is not: that 02:00-05:00 is the right London for your symbol and feed, that a real sweep
looks like the synthetic one (the exercise relaxes `sweepStrict` to make the raid branch reachable - audit
§17 has the arithmetic), and none of this is a claim about profit. The lines have been drawn by nobody but
pyne's interpreter: the paste, and one look at a real session, is still the test.


