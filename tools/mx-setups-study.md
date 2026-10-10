// NOT PINE CODE — this is a study note. The code it proposes is tools/archive/mx-context-overlay.pine
// (and the model script it must be paired with is tools/archive/cisd-ultimate-proper-v2.pine).

# ManipulationX v8 — what his indicator actually shows, and what we should build

Source: 13 screenshots from an NQ day-trader's week (5 graded setups + 8 raw chart frames), plus
3 hand-marked charts from you (NAS100 240M, XAUUSD 60M ×2). Everything below is split into **seen**
(the pixels) and **inferred** (what it must mean), because a video frame tells you the vocabulary,
not the algorithm. Where a feature is only in his *text overlay*, I say so — that matters, because
text he types in post-production is not evidence the indicator computes it.

## 1. Feature inventory (seen)

Distinguish the two layers. The blue banner ("MONDAY A+ SHORT"), the "Rated: A+" box and the bullet
lists are **video captions** — his own write-up. The chart furniture is the **indicator**.

| # | On-chart element | Seen in | Reading |
|---|---|---|---|
| 1 | `B` / `S` flag markers (green below, red above), each with a tiny price/time | all raw frames | the signal: bar where the model says enter, not where it armed |
| 2 | Filled **grey** boxes with right-edge labels `1H FVG`, `10am FVG`, `15M FVG+`, `10M FVG`, `iFVG`, `4H FVG` | frames 2, 4, 7, 9, 11 | an FVG **registry tagged by the timeframe it came from** — and by *when* it formed (`10am`), and its type (`iFVG`), and whether it's still unmitigated (`+`) |
| 3 | Filled **pink** boxes directly adjacent to the grey ones | frames 1, 2, 4, 7, 11 | the *opposite-side* array of the same move — his charts colour premium/supply pink and demand/discount teal (`TS`/`iFVG` boxes in your XAUUSD shots are the same convention) |
| 4 | Solid horizontal lines with text labels `DOL`, `9AM-H`, `LQP-H`, `Buy Side Liquidity`, `Sell Side Liquidity`, `Data low` | frames 1, 4, 9, 11, 13 + your charts | a **draw-on-liquidity ledger**: named pools, each with the anchor that defines it (9:30 open high, previous-session high, the low taken at the data release) |
| 5 | `$` `$ $` triple-tick glyphs sitting on a swing | frames 1, 2, 4, 6, 11 | the sweep itself: the tick count is the **touch count** of the pool that was just taken (3 ticks = triple equal highs) |
| 6 | Dashed horizontals through twin/trievel extremes | frames 1, 4, 5, 6, 12 | `relative equal highs/lows` — near-equal, tolerance-based, not exactly equal |
| 7 | Thin diagonal trendlines from the range origin, one labelled `Low Resistance … (LRR)` | frames 2, 4, 7 | the **low-resistance runway**: the open path to the next pool, drawn as a slope |
| 8 | `SMT w/ ES` labels with a short line joining two swings | frames 1, 4, 6, 9, 10, 11 | SMT divergence against the sibling index, annotated *at the divergence*, naming the pair |
| 9 | `0.5` line across a range | frame 11 | equilibrium of the dealing range (the fib-0.5 he requires for continuation: "DELIVERING FROM 0.5 FIB / AMD") |
| 10 | **Bottom-right table** — header `Bias | Bullish`, then `Checkpoint | Status`, then rows with `✓`/`✗` | frames 4, 8, 10, 13 | a **checkpoint panel**: a fixed list of named model conditions, each pass/fail, with a bias verdict in the header. This is the heart of the tool |
| 11 | A second pane with ES on the same timeframe, its own `B` marker | frame 10 | he reads NQ and ES side by side; the markers line up in time |

Not present anywhere on-chart: any A+/B+ grade, any reason list, any "Rated" string. **The grade is
his judgment, typed afterwards.** That single fact changes the design brief — see §4.

## 2. What the grade actually responds to (from his captions)

Ten graded bullets across five days, reduced to the factors he repeats:

| factor | appears | direction |
|---|---|---|
| delivering from an HTF FVG (4H / 1H / 30M / 15M) | 4× | **+** and it names the TF, so *which* TF is part of the quality |
| SMT w/ ES in the trade direction | 4× | **+** |
| clean / correct AMD, "AMD at open", "Judas shorts off open" | 4× | **+** |
| V-shape with displacement / momentum | 4× | **+** |
| abundance of low-resistance liquidity toward the target | 3× | **+** |
| equal highs/lows: triple equal + 9:30 wick, perfect equal lows, 3-touchpoint | 3× | **+** |
| iFVG + CISD (array *inversion*, not a fresh gap) | 2× | **+** |
| HTF equal highs above / sibling also in a distribution spot | 2× | **+** |
| **"No FVG delivery (bad)"** | **2×** | **−** and it cost a grade (A+→A−, B+) |

So his rubric is: **structure + array delivery + sibling confirmation + clean session narrative,
minus any missing delivery.** A grade is *demoted by a named defect*, which is a much more testable
statement than "score ≥ 4". Nothing in his tool computes it; his eye does. Which is exactly the
thing worth mechanising — the corpus already fixes the checklist
(`16-smt-divergence/index-smt.md`, `24-amd-cycle/amd-on-intraday.md`,
`02-liquidity/relative-equal-highs-lows.md`, `02-liquidity/low-resistance-liquidity-run.md`,
`05-pd-arrays/htf-pd-array-hierarchy.md`, `18-mitigation/partial-vs-full-mitigation.md`).

## 3. His five recurring setups, named

1. **HTF-array delivery continuation** — hold a 15M–4H FVG, price retraces into it in discount for
   longs, `0.5` of the range beneath it, V-shape with displacement, SMT at the extreme. Target = the
   first unmitigated pool in a low-resistance direction. *(Mon, Wed, the "trade of the day" frame.)*
2. **Equal-pool sweep → inversion** — triple/twin equal extremes taken, `iFVG` left behind, CISD in
   the same move; entry at the iFVG's CE, stop beyond the wick. *(Fri.)*
3. **Judas / AMD-off-open reversal** — the 09:30 open raids the pre-open (08:30–09:30) extreme, fails
   back, and the reversal *is* the A-phase trap; grade depends on whether the day's array was
   delivered afterwards ("No FVG delivery (bad)"). *(Tue, and the 1H scenario note.)*
4. **Data-day protocol** — 08:30/10:00 print makes a `Data low`/`Data high`; the first retrace back
   into the nearest array *after* the release is the trade; blackout rules apply into the print
   (`30-news-driven/cpi-protocol.md`, `news-blackout-rules.md`). *(Wed frame's `Data low`.)*
5. **Stop-run into array / turtle soup** — run the session or prior-day extreme, enter at the OB or
   FVG the run reaches. This is the one your own XAUUSD marks (`TS`, `iFVG`, `CISD`, `OB`) describe,
   i.e. what v2 is already built for.

## 4. Separate indicator. Not more inputs on v2.

The tempting move is to bolt all of this onto `cisd-ultimate-proper-v2.pine`. Don't, for four
concrete reasons, three of which are the failure modes this file has already been fighting:

1. **Object budget is per script.** v2 only became readable once level lines were rank-limited to
   2·N and arrays were deleted when spent. An HTF array registry across 4–5 timeframes, plus pool
   lines, plus SMT connectors, plus anchors, is another 60–120 objects *per bar of history* — you
   would re-create the exact clutter complaint inside one release.
2. **`request.security` and quote access are contagious.** SMT needs a second symbol (`ES1!`),
   HTF arrays need one call per timeframe. Those are the two constructs that make a script *fail to
   load* for reasons unrelated to logic (no data entitlement, a symbol that doesn't exist on the
   user's plan, a TF the feed doesn't publish). A model script that silently stops arming because a
   sibling symbol is unavailable is worse than a context layer that doesn't draw.
3. **Different cadence and different lifetimes.** v2 is a state machine (arm → fill → resolve →
   journal). Context is a *registry*: things get added, mitigated, expired; nothing resolves. Mixing
   them means the funnel/journal semantics get polluted by state that has no trade attached.
4. **The verification cost is asymmetric.** v2 is bounds-clean, gate-verified and documented. Every
   added data layer re-opens that whole audit for a feature you read off the side of the screen.

**So: `mx-context-overlay.pine` = the reading layer; `cisd-ultimate-proper-v2.pine` = the trigger,
risk and journal.** Pair them on the chart; the overlay deliberately never places a level, sizes a
trade, or grades a setup — it answers *"is there context, and how good is it"*. v2's `BLOCKED BY`
funnel answers *"why isn't there a trade"*. Those are different questions, and keeping them in
different files is the only reason both stay readable.

The one integration I recommend later, and it is small: give v2's score two of his factors as
optional points (`+1` delivery-from-HTF-array, `+1` SMT, each behind an input), because those change
*what you take*, not what you see. That's a v2 change on its own merits, not a merge of the two
files — and it should come only after the overlay's checkpoint flags prove stable on your charts.

## 5. Spec built (and what is deliberately out)

`tools/archive/mx-context-overlay.pine`, per the inventory: array registry with TF + age + type labels and
mitigation state; near-equal pool clustering with touch counts and swept state; session/news anchors
with a `DOL` line for the highest-probability draw; premium/discount equilibrium of the intraday
dealing range; Judas/manipulation detection inside the open window; SMT divergence vs a configurable
sibling with a tolerance in ticks; a low-resistance runway count toward the first pool beyond the
entry; and a `Bias | Checkpoint | Status` table with ✓/✗ per checkpoint and the *failing* one named,
in the same spirit as v2's `BLOCKED BY`.

Out of scope, with reasons:

* **The A+/B+ grade as an output.** Not yet. His grade weights "the narrative made sense" — I can
  count his factors but I can't verify his weighting, and a fabricated 0–10 "quality score" is the
  single most common way these tools become decoration. It ships as a *count of passed checkpoints*
  and a named defect list; if you want a grade after a month of comparing it to your own labels, we
  calibrate it against those instead of inventing it.
* **News timestamps.** Pine has no economic-calendar access; `Data low` is therefore anchored to the
  configurable print times (08:30 / 10:00 NY), not to an actual release.
* **Hand-drawn scenarios** (his arrows and "Scenario 1/2/3" notes) — that's charting, not computing.

## 6. Running it

Two scripts on the chart. `MX Context Overlay` top-right (context), `CISD Ultimate v2` dashboard
bottom-right (trigger, risk, journal). They never contradict each other because they never answer the
same question: if the overlay says the context is good and v2 has nothing armed, that is *"no setup
yet in good context"* — which is the correct answer most of the time. If v2 arms and the overlay's
`Defects` row is long, that is a **pass-on-your-part** signal, not a bug in either script.

Presets, from the charts you actually sent:

| chart | HTF slots | sibling | pivot length | notes |
|---|---|---|---|---|
| NQ, 5m or 15m | 240 / 60 / 15 | `ES1!` | 6 | his default. Turn SMT on only if you have CME data for ES. |
| NQ, 1m | 60 / 15 / 5 | `ES1!` | 3–4 | drop `arrMin` to ~0.15 or the 5M arrays filter away. |
| XAUUSD, 60m (your hand-marked chart) | `D` / 240 / 60 | `DX-Y.NYB` | 8 | gold's session anchors are not 08:30/09:30 NY futures times — set the open inputs to your broker's London/NY overlap, or blank the data window and ignore the Judas row. |
| NAS100, 240M | "" / "" / `D` | `ES1!` | 10 | at 4H+ every chart bar is an HTF bar for the next slot; leave two slots blank so you do not draw the same gap twice. |

Reading order, in the order his own notes weight them: **FVG delivery** (the only item he ever wrote as
`(bad)`) → **Reacting from array** → **AMD / Judas run** → **SMT confirm** → then the two target-side
rows (**Pool ahead**, **Runway**) and the **0.5** position. `Passed n/7` and the grade string are a
count of those, nothing more.

Calibrate before you trust it, and it takes one week: every day, write down your own letter for the
day's best setup, and note what the panel's `Passed` count was at that bar. If your letters and the
count do not move together after ~10 samples, the weighting is wrong — and then we know *which* row to
fix, which is more than any grade could tell you. That comparison is the only legitimate path to an
automatic A+/B+ grade; §4 explains why I would not invent one now.

## 7. Verification record for the overlay (read this before blaming a flag for being wrong)

The first version of this file compiled clean under `pyne check` and was rejected 63 times by
TradingView. 62 of those were one construct: `arr[i]` indexing sugar on a global array used *inside a
function or any indented block*, where the name resolves to the whole array instead of its element. At
column 0 the sugar is accepted; one indent deeper it is not. The overlay therefore uses `array.get` /
`array.set` for every collection access inside a block, which is also what v2 had always done — my
note that "v2 uses `px[i]`" was a misreading of `high[k]`, the *historical* operator on built-in
series, which is a different feature wearing the same brackets.

Also fixed in this pass, all classes rather than spots: a `barstate.is_last` typo (the member is
`islast`), `ta.atr` called from inside a ternary (series must advance every bar), an `int` element
inside a `request.security` tuple that the reference runtime returns as 0 (the new-array test is now
a per-side value-change memory instead), and the array element assignments moved to `array.set` after
the reference runtime's numeric path failed on the sugar form.

**Gates, in order:** `bash tools/pine-lint.sh tools/archive/mx-context-overlay.pine` → **clean** (this is the
TradingView-parity type checker; run it first, always) · `python3 tools/pine-validate.py` → 0 findings,
with `--selftest` firing all 8 rules · `pyne check` → OK · `pyne run` on a plumbing-shimmed copy →
arrays settle at exactly `arrKeep·2` and pools at `poolKeep·2`, so the add/mitigate/expire/trim/delete
lifecycle holds its caps.

**What that does NOT prove:** that a 4H array was found on Tuesday. The reference runtime's synthetic
bars are contiguous (`low > high[1]` never true), so a genuine 3-bar gap cannot exist there and
`ta.pivothigh` returns na — the FVG and pivot paths only *execute* there, they cannot be *scored*.
Nothing here is a signal-rate claim: the panel's `Passed n/7` and the grade string are a count, and §6
is the week-long comparison against your own letters that would earn the right to call it a grade.
