// NOT PINE CODE — this is a markdown guide. Do not paste it into the Pine Editor.
// The script it documents is: tools/archive/cisd-ultimate-proper-v2.pine  (that file is the code).

# CISD Ultimate v2.1 — how to use it, settings per timeframe, and the setups worth taking

`cisd-ultimate-proper-v2.pine` is not a signal box. It is the 2022 ICT model written down as a
state machine: it maintains a liquidity pool, waits for a raid, scores the shift that follows,
arms a setup at the array left behind, and then journals what happened so you can find out
whether *your* instrument respects *your* settings. The judgment — should I be long today at
all — stays with you, because Pine cannot read a weekly chart.

Everything below is ordered by how much it changes your results.

---

## 0. Two-minute start

1. Open a 5-minute chart of an index futures CFD or FX major (NQ/MNQ, ES, EURUSD, GBPUSD). These
   are what the model was built for: 24h data, real session opens, pools that get raided.
2. Add the indicator. Leave `Preset` on **Auto (chart TF)**.
3. Set `HTF bias → HTF timeframe` to the row below (15 for 5m charts).
4. Turn on `Alerts` with the static condition, or `alertOn` for the JSON payload (§6).
5. Scroll back 2–4 weeks and read the journal table before you trust anything (§7).

### Density — the one switch that decides what the chart shows

The model reads every pivot, gap and block it can find. The chart does not need to see them, and
showing them is what turns a tool into wallpaper. **`Density`** decides how much is drawn, and it is
set independently of what the model uses:

| | Minimal | **Clean** (default) | Full |
|---|---|---|---|
| Level lines | 1 per side | 3 per side, only within 8 ATR | every tracked pivot (24/side), extended right |
| FVG / OB boxes | while fresh only | while fresh only, deleted when spent | kept, dimmed when spent |
| Delivery line | off | off | plotted across the pane |
| Dashboard | 4 rows | 4 rows | 9 rows |
| Journal | 5 rows | 5 rows | 13 rows |

* A level stops being a line the moment it is no longer one of the nearest pools — the *data* stays
  in `lvPx`/`lvSt` and keeps driving the model, only the drawing is rank-limited. That is the whole
  trick: what is on screen is bounded (≤ 2·N lines) no matter how long the chart or how fast the
  timeframe, because lines are created when a pool becomes relevant and deleted when it stops being.
* Boxes track their right edge only while they are live. In v2.1 they were built with
  `extend = extend.right`, so every gap ever drawn stayed a full-width band — those pale stripes
  across the middle of the chart were never information, just accumulation.
* Panel cells paint their own background and the tables have no frame or grid: a row the mode does
  not use is invisible instead of an empty band, which is what makes a 4-row panel *look* like
  4 rows. And text never gets transparency — only backgrounds do. Translucent value colours on a
  dark panel were the reason the old table read as mud.
* `Pools drawn per side` (0 = from density) and `…only within this many ATR` are the two knobs if
  Clean is still too busy or too spare. The ATR cap is the honest one: a pool 60 ATR away is not a
  draw on liquidity, it is a footnote from a different market phase.

Default state: London + NY AM killzones, Asian range built, PDH/PDL pools live, HTF alignment as
**Soft** (score, not veto), **Any raid** sweep gate, frame gate on, entry at CE (50% of the array),
stop beyond the sweep, target at the nearest opposite pool, risk capped at 5 ATR, score floor 2/6.

Four of those are new since v2.1 and they exist because a veto stack that silences the indicator is
worse than a looser one: `HTF alignment` (Off / Soft / **Veto**) and `Killzone` (Off / Score only /
**Veto**) are now separate from the score, and the score is *always* computed from the facts, so a
grade means the same thing whichever gate mode you choose. `Sweep before the shift` went from a
yes/no checkbox to Off / **Any raid** / Opposite raid: "opposite raid" is the judas-swing reading and
the tighter one; "any raid" is what the 2022 model actually says (take liquidity, then shift).

---

## 0c. "No setups and an empty journal" — the two state bugs that caused it

If your chart looked like this — `RAID none`, `SCORE —`, `SETUP —`, `JOURNAL 0` — the model was not
being too strict, it was **incapable of completing its own chain**. Two defects, both fixed in v2.3:

1. **The raid was forgotten before the shift it authorises.** `raidSide/raidPx/raidBar` and
   `brokeSide/brokePx/brokeBar` were declared without `var`. A non-`var` global is re-initialised on
   every bar, so `raidBar` was back to `-1` the moment after the bar that set it. The candidate
   capture (`pRaidBar := raidBar`) ran on the *break* bar, so a setup could only qualify if the sweep
   and the break happened **on the same bar** — and the level loop spends a level in exactly one of
   those two branches, so it essentially never did. That is the whole of steps 3→4 of the 2022 model,
   dead: no `gSweep`, no `gShift`, nothing armed, nothing journalled. The smoking gun was on the
   screen the whole time: a chart that did show a raid read `RAID BSL 0b` — a raid *zero bars ago*,
   every single time. Raids are supposed to be 1…`sweepWin` bars old; `0b` was the reset, not the
   market.
2. **`ta.pivothigh(swLenF, swLenF)`** passed a length where the documented signature wants
   `(source, leftBarCount, rightBarCount)`. TradingView resolves the two-argument form the way the
   script wanted; the reference toolchain reads the first argument as `source` (a constant, which is
   never a pivot) and every level array stays empty forever. The call now names `high`/`low`
   explicitly, so the script means one thing to every compiler.

Everything else in this file is taste; these two were broken plumbing. If you are still on v2.1 or
older and your journal is empty, do not tune `dispMin` — re-paste.

## 0d. Reading the funnel when setups are still rare

The panel row **`BLOCKED BY`** and the journal row **`CANDIDATES / ARMED / FILLED`** now count every
stage since the first loaded bar, and `BLOCKED BY` names the stage where the most candidates die
(`sweep 9 to 3`, `risk 4 to 1`, …). Turn the tooltip on any of those three cells to read the whole
chain. This is the difference between a strict model and a broken one, and you should never have to
guess which you are looking at:

| `BLOCKED BY` says | What it means | What to do |
|---|---|---|
| `no breaks in view` | no confirmed close through a swing in the loaded range | load more history, or lower `Swing pivot length` |
| `displacement A→B` | breaks happen, they are not forceful | lower `Min displacement score`, or move to a higher timeframe |
| `sweep A→B` | breaks with no raid nearby | `Sweep gate` → `Any raid` (default) or `Off`; widen `Sweep must precede…` minutes |
| `reclaim A→B` | the break is being closed back through the level | it is working; a reclaimed break is not a CISD |
| `risk A→B` | stop sits beyond `Max risk (ATR)` | raise it (metals on 5m often need 5–6), or accept that the sweep was too far |
| `score A→B` | surviving candidates are thin on confluence | `Min confluence score` 2 → 1 loosens, 3 tightens |
| `killzone veto A→B` | everything else passed, the clock said no | `Killzone` → `Score only`, then read `EXP OFF` in the journal before you keep it |
| `arming ✓` | setups are firing | nothing |

## 1. The chain, as a checklist

This is the whole model. The indicator walks it top to bottom; you should be able to say each line
out loud before you click.

| # | Condition | Script's gate | Concept file |
|---|---|---|---|
| 1 | Draw on liquidity is clear | `HTF bias` cell + the dealing-range `FRAME` cell | `05-pd-arrays/dealing-range.md` |
| 2 | Price is inside a live killzone | clock block, `CLOCK` cell | `10-killzones/killzone-times-table.md` |
| 3 | A *specific* pool was raided | `RAID` cell, `needSweep` | `02-liquidity/liquidity-sweep.md` |
| 4 | The raid is confirmed by a wick, not a body | `wickMin` 0.60 + `needBack` | `02-liquidity/liquidity-sweep.md` |
| 5 | The counter-move is a displacement | `DISPLACEMENT` ≥ `dispMin` (9/15 on 5m) | `09-displacement/displacement-strength-criteria.md` |
| 6 | It leaves an array behind | FVG ≥ `fvgMin` ATR, or iFVG, or a framed OB | `06-fair-value-gaps/fair-value-gap.md`, `07-order-blocks/order-block-criteria.md` |
| 7 | The array sits in the right half of the range | `needFrame`: discount for longs, premium for shorts, OTE bonus | `27-equilibrium/` |
| 8 | Entry on the retrace | `entryDepth` = CE, armed for `armWinMin` | `06-fair-value-gaps/ce-as-primary-entry.md` |
| 9 | Stop beyond the sweep; target the opposite pool | `slMode` / `tpMode`, floor 1R | `32-risk-management/r-multiple.md` |
| 10 | It gets journalled | every resolution writes a row | *(no concept file — the script's own ledger)* |

**The order is the edge.** A sweep with no displacement is noise; displacement with no array is a
gap you cannot enter; an array outside the frame is a trap. The dashboard's `SCORE` cell is those
six weighted checks (sweep · strong displacement · frame · HTF · array · time), and `A` needs
displacement ≥ `dispA`, not just a high count.

---

## 2. Timeframes: the ladder is now automatic

v2.1 reads `timeframe.in_seconds()`, picks a row, and converts every window you entered in
**minutes** into bars. You no longer retune the whole script when you change TF, and a bar count
that only made sense on 5m can no longer silently break a 1H chart.

What each row resolves to with default inputs (0 on `Swing pivot length`, `Min displacement score`,
`'Strong' score`, `Min FVG height` means "take it from the row" — type a number to override):

| Chart TF | row | pivot len | disp min / A | min FVG (ATR) | level expiry | array valid | armed for | sweep within | cooldown | max hold |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 min | 0 | 12 | 10 / 12 | 0.30 | 600 b | 120 b | 90 b | 60 b | 30 b | 360 b |
| 3 min | 2 | 10 | 10 / 12 | 0.25 | 200 b | 40 b | 30 b | 20 b | 10 b | 120 b |
| 5 min | 3 | 10 | 9 / 11 | 0.25 | 120 b | 24 b | 18 b | 12 b | 6 b | 72 b |
| 15 min | 5 | 9 | 9 / 11 | 0.25 | 40 b | 8 b | 6 b | 4 b | 2 b | 24 b |
| 30 min | 6 | 8 | 8 / 10 | 0.22 | 20 b | 4 b | 3 b | 3 b | 1 b | 12 b |
| 1 hour | 7 | 8 | 8 / 10 | 0.20 | 12 b | 4 b | 2 b | 3 b | 1 b | 8 b |
| 2 hour | 8 | 8 | 8 / 10 | 0.20 | 12 b | 4 b | 2 b | 3 b | 0 b | 8 b |
| 4 hour | 9 | 7 | 8 / 10 | 0.20 | 12 b | 4 b | 2 b | 3 b | 0 b | 8 b |
| 1 day | 10 | 7 | 8 / 10 | 0.20 | 12 b | 4 b | 2 b | 3 b | 0 b | 8 b |

`TF / WILSON` in the journal table prints the row it chose and the resolved bars — read that cell
instead of trusting this table if you have changed anything.

Two notes on the shape of the ladder:

* **The displacement gate gets *looser* as the timeframe rises (10 → 8) and the pivot length gets
  *shorter* (12 → 7)** — not a typo. The 5-factor rubric is absolute, and a candle's range grows
  with the timeframe, so the same 9-point bar on a 1H chart is a far stronger statement than a
  9-point bar on 1m. The pivot length shrinks because a 1H swing needs fewer legs to be a swing;
  demanding 12 candles each side on a 4H chart means you only ever see weekly levels.
* **Above 1H the minutes stop being the point.** `12 b` for expiry is the floor, not the
  conversion — on coarse charts a duration like "10 hours of level life" is meaningless, so the
  script falls back to "enough bars for the test to exist". If you trade 4H/D and want a real
  lifespan, express it in the timeframe's own units: `Level expiry (minutes)` = 43200 is 30 days.

---

## 3. Settings by timeframe — the part the ladder cannot decide

### 1m / 3m / 5m — execution timeframes

This is what the script is *for*: you already know the direction, you are finding the entry.

* `Killzone set`: **Public 2022 set**. `sigLondon` + `sigNyAm` on, everything else off unless you
  specifically trade the close. Turn `useSb` on if you only want the Silver Bullet hour (it
  replaces the window, it does not narrow it).
* `HTF bias`: 15 (5m chart) or 30 (1m chart). `htfMode` = **Close vs EMA**, `htfEma` 50.
* `tpMode` **Nearest pool**, `rrFixed` 2.0 if you use `Both`.
* `Level expiry` 600 min is right; on 1m consider 360 so overnight levels do not clutter.
* Expect 1–4 setups a day per instrument. If you get 10+, `minScore` is 2 — raise it to 3 and
  put `needFrame` back on.

### 15m / 30m — the day-trading chart

The one place the model works as a *standalone* system rather than an entry timer.

* `HTF bias`: **60** for 15m, **120–240** for 30m, and prefer `Position in HTF dealing range` —
  on these charts "above/below equilibrium of the last 30 HTF bars" is closer to how ICT actually
  framed a day than an EMA is.
* Keep both killzones plus `sigLc` off; the London-close window on 15m is mostly chop (its two
  hour bar-range is the reason `cool` goes to 1–2 bars).
* `Min FVG height`: 0.25 is fine at 15m; if you trade a thin CFD, 0.30 cuts the noise.
* `entryDepth`: **CE (50%)**. On 30m, `Near edge` costs you more fills than it saves in price.
* Expect 0–2 a day. If the journal says `ARM→FILL` is worse than 1-in-4, your `armWinMin` (90) is
  too short for this TF: 120–150.

### 1H — intraday swing / overnight

* `HTF bias`: **240**. This is the timeframe where "alignment" starts to matter more than timing,
  so leave `htfOn` on even if you turn it off lower down.
* Killzones become advisory: 1H bars are 12 of the 20 London hours, so a `02:00–05:00` filter
  mostly rejects *late* signals rather than *bad* ones. Try `Killzone set` = **No filter** with
  `minScore` 4 and read which one journals better (§7). That is a genuine, testable question —
  the `EXP OFF` cell exists precisely to answer it.
* `Level expiry` 600 min (10 h) and `array valid` 120 min become floor-bound; set them explicitly
  in hours if you care (e.g. expiry 2880 = 2 days).
* `maxHold` = 8 bars: at 1H that is 8 hours, i.e. a position that did not do anything by the end of
  the session is closed at market and journalled as a time-out. That is intentional — holding
  hoping is how ICT descriptions turn into bag-holding. Raise `armWinMin` if you want more room.

### 4H / 1D — bias and planning, not entries

* Do not take entries here. Use the script to mark the pools and arrays that the 5m/15m chart will
  later react to: `showSwings` + `showFvg` + `showOb` on, `alertOn` off, `btOn` off.
* If you still want signals: `preset` = **4H**, `minScore` 3, killzones **off** (the clock has no
  meaning on a 4H bar), `needShift` on, `tpMode` **Fixed R** at 3R, `poolExpiry`… there is none —
  PDH/PDL and the Asian range are per-session by construction, which is exactly why they expire on
  their own on these charts.
* Expect a handful of trades per *month*. The `n too small` verdict is the honest one for months.

### Crypto / 24h instruments

The clock is defined in New York time (`Session timezone` — keep it, the killzones are NY-based by
definition, `10-killzones/killzone-times-table.md`). On a 24h market the Asian window is genuinely
meaningful (Asia 20:00–00:00 NY = 01:00–05:00 UTC, real volume in BTC/ETH), and `sigNyPm` +
`useMacro` is worth testing. But `wickMin` 0.60 is too strict for a 24h coin: 0.45–0.50, because
thin-book wicks are not liquidity pools.

### Expiry / low-volume CFDs and small caps

Turn `htfOn` **off**, raise `dispMinIn` to 11–12, and set `btCost` 0.10–0.15 R. Spreads on those
instruments are a fixed tax per trade and the journal only tells you the truth if you charge it.

---

## 4. The setups worth taking

In priority order. All five are inside the script; the difference is which cells you want green.

References: `14-asian-range/asian-range-sweep.md`, `13-judas-swing/london-judas-swing.md`,
`11-silver-bullet/silver-bullet-rules.md`, `17-optimal-trade-entry/ote-62.md`, `25-htf-bias/daily-bias.md`.

**1. London Open Raid → 09:50 retrace (the one).** SSL taken at 02:00–02:30 NY, displacement up
≥ `dispMin`, FVG in discount, entry at CE, stop under the sweep low, PDH or the Asian high as the
target. Highest hit rate because the pool is *unambiguous* — everyone is looking at the same Asian
low. `RAID` cell must name the pool; "swept level only" in `SCORE` means it was a swing, not a
session extreme, and you take 1 point less.

**2. NY AM CISD at the day's high.** London ran up, took PDH or the London high between 08:00 and
08:30, then the 09:30 equity open pushes one last tick above it and the *first* down-close 5m bar
that breaks that bar's low is the shift, with an FVG at or above equilibrium. Short into the gap,
stop above the sweep high, target the London low / the day's open. This is `13-judas-swing/ny-judas-swing.md` in trade form; the `+OTE` flag in the `FRAME` cell means the retracement is still inside
the 62–79% band, which is where you want to be short.

**3. Silver Bullet inside a range day** (`11-silver-bullet/silver-bullet-ny-am.md`). 03:00–04:00 or 10:00–11:00 NY, no fresh pool within 1.5×
ATR, an array in the correct half, entry at CE. Lower expectancy *by itself*; it is the best
execution window for setups 1 and 2, and that is the way to use it (`useSb` on).

**4. London-close continuation** (`13-judas-swing/london-close-judas-swing.md`). Trend day, price took liquidity on the *wrong* side at 10:00,
and the 10:30–11:30 retrace into the last 1H FVG is the last entry in the day's direction. Only
take it with `HTF` matching and score ≥ 4; this pattern is the one that dies without a real trend.

**5. 4H/1D array + 5m confirmation (the swing)** (`25-htf-bias/bias-confluence.md`). On the 4H chart, note the FVG that formed after
a raid of a weekly high/low. On the 5m, wait for the script to arm in the same direction *inside*
that 4H array. Score 3 is enough here, because the timeframe alignment is doing the work the score
would otherwise have to do.

**Never take:** score < `minScore`; an `ARM` with `NO ARRAY` as the reason (the journal cell exists
so you can see that bucket is worse); a setup that armed outside the clock when `CLOCK` says
`out`; anything while `SETUP` still says `armed` — armed is not filled (§5).

---

## 5. Managing the trade

* **Entry.** The script draws a dotted line at CE when it arms and marks `FILL` when price trades
  into it. That is the only moment it is a trade. `ARM→FILL` in the dashboard is your fill rate —
  a low one means `entryDepth` is too passive for your volatility, not that you are unlucky.
* **Stop.** `Beyond the sweep` (default) — the level you are fading, with `atrBuf` 0.35 on the ATR
  variant. If a stop has to be wider than the array plus buffer to survive, the array was not the
  reason for the trade. `Displacement of HTF structure` is the right gate on
  15m+; on 1m use the sweep extreme.
* **Target.** `Nearest pool` first, `Both` if you want a fixed 2R as a partial. `CLIP ≥2R` in the
  journal next to `AVG MFE` is the test: MFE far above your target while the ≥2R bucket is thin =
  your TP is cutting the tail off a distribution that pays you in tails.
* **Time.** `maxHold` = 4× the arm window after the fill; a time-out is closed at the close and
  journalled. Do not override this in review — the time-out rate is information about the setup.
* **One at a time.** `allowBoth` off means an armed setup blocks the opposite direction. Turn it on
  only if your journal shows a real hedge behaviour on that instrument; for almost everything it
  converts a model into a coin flip.
* **After a resolution** there is a `cool` cooldown (30 min default). It exists to stop the same
  raid being re-scored three bars later off a slightly different array.

---

## 6. Alerts

Two mechanisms, use both:

* **Static** (`alertcondition`, already in the script): *CISD Ultimate — setup armed*, *— setup
  filled*, *— target hit*, *— stopped or voided*. Create the alert with "Once Per Bar Close" and
  the message can use `{{close}}`, `{{ticker}}`, `{{interval}}`.
* **Dynamic** (`alertOn` → `Emit alert() events with a full payload`): one alert on the
  *"Any alert() function call"* condition gets you `ARM / FILL / TP / SL / VOID` with the whole
  trade in the message — JSON by default:

  ```json
  {"event":"FILL","symbol":"NQ1!","tf":"5","dir":"long","grade":"A","score":5,
   "array":"FVG","entry":20145.25,"sl":20112.50,"tp":20222.75,"targetR":2.0,"bars_ago":3}
  ```

  `entry`/`sl`/`tp`/`targetR` are enough to place an order without looking at the chart, and they
  are the fields to forward to a webhook. TradingView's rate limit is ~15 alerts per 3 minutes, and
  the JSON is only as good as the state at the close of the bar that fired it — which is why the
  payload is emitted on `barstate.isconfirmed` and never intra-bar.
* Do **not** wire an auto-execution bot to `ARM`. `ARM` means "waiting for a retrace"; the order
  belongs on `FILL`.

---

## 7. Reading the journal, and the tuning protocol

The bottom-left table is a per-trade ledger (net R after `btCost`, no simulated fills — it assumes
you got filled at the drawn entry) plus the aggregates:

| Row | What it is | How you act on it |
|---|---|---|
| TRADES / WIN RATE / EXPECTANCY | `n`, wins/losses, net R per trade | < 30 trades is not a read |
| STREAK / MAE / MFE | worst run, avg max-adverse, avg max-favourable (R) | `AVG MAE > 1R` → the stop is inside the noise |
| AMBIGUOUS / TIMED OUT | same-bar TP+SL, `maxHold` exits | timed-out > 30% → the setup's move is earlier than your window |
| WIN RATE vs BREAK-EVEN | the arithmetic floor at your avg R | `32-risk-management/r-multiple.md` |
| **VERDICT** | **Wilson 95% lower bound on the win rate vs break-even** | `not proven` is the correct answer for most settings; `edge holds` is rare and worth sizing |
| TF / WILSON | the row picked + resolved bars + the bound | the audit trail for what you actually tested |
| EXP ASIA / LONDON / NY AM / LC-PM / OFF | net R per bucket, with n | if `EXP OFF` beats the killzones, the clock is decoration for this instrument — stop paying it rent |
| NO ARRAY / FVG / iFVG / OB | net R per array kind | the kind with negative expectancy is the kind you delete from your plan |
| R HIST / TAIL ≤-2R / CLIP ≥2R | distribution of results | a fat left bucket means the stop is being taken by the move it is supposed to sit beyond |

**Protocol.** Change exactly one input. Watch 30 journalled trades (or re-run the same settings over
a fixed `Lookback bars`, so the comparison is apples to apples). Keep the change if `EXPECTANCY`
improves *and* `VERDICT` does not get worse *and* `EXP LONDON`/`EXP NY AM` did not become the only
positive cells (a setting that works only in one window is a curve fit). Write the change down next to the settings that produced
it — this corpus has no journaling concept file yet (worth fixing), but the discipline is not
optional either way.

The order I would tune in, because that is the order that moves expectancy most:
`minScore` → `entryDepth` → `dispMin` → `armWinMin` → `tpMode` → everything else.

---

## 8. What is deliberately *not* in the script

The temptation with an indicator like this is to keep adding confirmation until it feels safe.
These were considered and rejected, and knowing why is part of using it:

* **`strategy()`-based fill simulation.** The journal applies the model, not a broker: no spread,
  no slippage beyond `btCost`, no partial fills, no intrabar ordering beyond the `Same-bar TP & SL`
  rule (`Count as loss` / `Count as win` / `First-touch heuristic`, which uses the bar's own
  open/high/low geometry). The honest fix is a second script wrapped in `strategy()` with
  `process_orders_on_close=true`; it is not done here because a `strategy` cannot be layered on the
  same chart as this indicator without doubling the drawing budget, and because a backtest you
  have not emotionally audited is worse than none.
* **Multi-timeframe auto-bias** beyond the single `request.security` HTF read. Nine `security()`
  calls per bar is the compile limit, and stacking monthly/weekly/daily/4H/1H into one boolean
  produces a number nobody can attribute to anything.
* **Win-rate or "smart money" scoring gauges that predict**. The score exists to gate entries, and
  it is already in the `SCORE` cell.
* **Repainting resolution.** Setups arm and resolve on `barstate.isconfirmed`. An `ARM` line you saw
  mid-bar can vanish — that is the price of not repainting, and it is why alerts fire on bar close.
* **Dynamic `ta.*` lengths** where Pine forbids them (`dispLook` feeding `ta.sma` needs a
  `simple int`, so it stays in candles — and factor 3 of the displacement rubric is a *relative*
  measure, so candles are the correct unit for it anyway).

---

## 9. Known limits

* **Line numbers in TradingView's console do not match this file.** The compiler reports offsets
  inside `#main()`, which sits ~50 lines below the file's own numbering. Locate an error by the
  construct it names, not the number.
* **`max_bars_back`.** The displacement score and the OB framing read history at a computed offset,
  so on a chart scrolled back to a hard `max bars` limit TradingView can complain about the series
  length. The remedy, if and only if you see it, is one line after `var float[] avgBody = ...`:
  `max_bars_back(avgBody, 20)`.
* **Sessions reset, pools do not persist across a weekend.** PDH/PDL are rebuilt per day, the Asian
  and London ranges per session; a level from Friday's NY PM is still a pool on Monday morning if
  it is still inside `expiry`. That is correct behaviour for the model and surprising behaviour
  for a person.
* **The resolved-trade markers (the `Mark resolved trades` input) are drawn on the last bar only**, so they are a review aid, not
  a tick-by-tick replay. `markN` 0 turns them off; the label budget is `max_labels_count` = 500.
* **The indicator was validated offline, not on a live feed**: syntax, local/global scope,
  tuple arity, array-type inference, loop-bound safety, and execution over 250–1500 synthetic bars,
  for this file and both earlier iterations (`cisd-ultimate-balanced.pine`,
  `cisd-ultimate-journal.pine`, which received the same loop-clamp sweep).
  `tools/cisd-audit.md` §5–§7 records the checks and what they cannot prove.

---

## 10b. v2.2 — the clutter pass

Prompt: *"Too cluttered. Let's do a better work."* What changed, measured on the chart that was
pasted (XAUUSD 5m):

| | v2.1 | v2.2 (Clean) |
|---|---|---|
| horizontal level lines | up to 48, each extended to the right edge | ≤ 6, finite, rank-selected against the close |
| FVG/OB boxes | every one ever made, extended to the right edge | only the live ones, closed the bar they are spent |
| full-width delivery plot | always | Full density only |
| panel cells | 32 (dashboard) + 78 (journal) | 16 + 30, same headline facts, opaque text |
| inputs you must reason about | 8 display toggles | 1 density switch + 2 refinements |

Nothing was moved off the model to get there: `hideSpent`, `showSwings`, `showFvg`, `showOb` still
behave exactly as before, `Full` reproduces v2.1 pixel for pixel, and the journal's 13 rows are all
still computed — 8 of them simply only render when you ask for them. The `SETTINGS` row (Full)
prints the resolved ladder so a screenshot of the panel is enough to reproduce a result.

## 10a. v2.3 — the chain was dead, and the panel now says so

* **Fixed:** raid/break state (`raidBar`, `brokeBar`, …) is `var` now, so the sweep survives to the
  bar where the shift is judged. This is what makes `gSweep`/`gShift` reachable at all.
* **Fixed:** `ta.pivothigh/pivotlow` take `(high|low, left, right)` explicitly instead of a
  two-argument form whose meaning differs between compilers.
* **Added:** a stage funnel (`CANDIDATES/ARMED/FILLED` in the journal, `BLOCKED BY` in the panel),
  counted since the first loaded bar — §0d explains how to use it as a tuning order.
* **Changed:** `Require HTF alignment` → `HTF alignment` (Off/Soft/Veto, default **Soft**),
  `Chain: liquidity sweep` → `Sweep gate` (Off/Any raid/Opposite raid, default **Any raid**), new
  `Killzone` gate mode (default **Veto**), new `Max risk (ATR)` (default 5.0, was hard-coded 4.0).
  The veto and the score are now decoupled: switching a veto off never inflates a grade.

## 10. v2.1 changelog (what changed from the file you had)

1. **Timeframe auto-ladder** (`Preset = Auto (chart TF)`) and every clock window re-expressed in
   minutes: level expiry, array validity, arm window, sweep-before-shift window, cooldown. Bar
   counts above 1H now fall back to sane floors instead of silently degenerating.
2. **Three dead inputs fixed**: `Levels tracked per side` was declared and ignored (hard-coded
   40) — now wired; `Frame a same-colour run as ONE block` did nothing — it now sets the framing
   run to 1 candle when off; `Session/day pool stays live (bars)` never existed as a mechanism,
   and it is removed rather than faked (pools expire by session construction, §9).
3. **Journal depth**: every trade now carries its killzone bucket and its array kind, and the table
   gained per-zone, per-array-kind expectancy, an R-multiple histogram with tail/clip counters, and a
   **Wilson lower bound** driving `VERDICT` so a 12-trade 67% cannot read as an edge.
4. **`alert()` payload** (JSON or plain text) with event, dir, grade, score, array kind, entry/SL/TP
   and target R, emitted on bar close only.
5. **Resolved-trade markers** on the chart (`showMarks`, `markN`), built and rebuilt inside the last
   bar so the object budget stays flat.

## 10c. v2.4 — the compiler round (nothing about the model changed)

TradingView rejected v2 with 5 errors that my previous gates had missed. They are all *plumbing*, so
the strategy, the gates and the numbers in §1–§9 are untouched:

* **Input group labels are declared at the top now.** `group=grpR` referenced a label declared eight
  lines further down, and a name is only visible after its declaration line. Same for the other nine.
  You will see no difference beyond the input panel keeping its sections.
* **`BLOCKED BY` gained its right-hand cell: `CANDIDATES n`.** The row was built with 6 of
  `f_jrow2`'s 10 arguments, which is a compile error — and once it compiles, the new cell is the one
  that tells you whether the funnel rejected everything (`CANDIDATES 57`, turn a gate) or never saw
  anything (`CANDIDATES 0`, check you are on a chart with enough bars and the right timeframe).
* **The journal table's row cursor is `jrow`, not `jr`.** `jr` was a local shadowing the global array
  of per-trade returns. A cell in that block reads `jrow + 1`; the row count is still right.
* **v1 files repaired too** (`cisd-ultimate-journal.pine`, `cisd-ultimate-balanced.pine`): their HTF
  bias now reads the last *closed* higher-timeframe bar instead of the forming one (that was a real
  repaint, and it is why their 1H bias wobbled intrabar), the two conditional `ta.highest/lowest`
  calls are hoisted, and a dead `Show Normal CISD lines` checkbox is gone.

**Reload both scripts** — TradingView keeps the compiled version of an already-added indicator, so an
edit that fixes a compile error still shows the old behaviour until you remove and re-add it (or press
Update on the indicator). And from now on the gate order is `bash tools/pine-lint.sh tools/*.pine`
first: it is the one that is actually TradingView's type checker. See the audit, §11.

## 10d. v2.5 — the two tables stopped repeating each other, and the blocker names the knob

Same model, same defaults, same alert conditions. Nothing about the trade logic changed. Three edits,
all about reading the thing on a small chart:

- **`BLOCKED BY` is actionable now.** It used to name the stage where the most candidates die
  (`killzone veto 286 to 12`). It now ends with the input that loosens that stage:
  `killzone veto 286 to 12 · kzGate`. Stages with no knob say `definitional - no knob` rather than
  sending you hunting for one (shift order and premium/discount are the model, not a filter).
- **The funnel lives in exactly one place.** The journal's `CANDIDATES / ARMED / FILLED` row is gone —
  it duplicated the dashboard and the journal is a trade-outcome table. The dashboard's right pair is
  now `FUNNEL 286 → 2 → 2` (candidates → armed → filled), and the journal shrank from 6×14 to 6×12
  rows, so the whole table is two rows shorter.
- **The title carries a build tag** (`CISD Ultimate - Proper (v2) - build 2.5`) because TradingView
  caches the compiled build per script name: after an edit the legend is the only way to know you
  actually re-added the new file. Delete the old instance first.

Numbers on the XAUUSD 5m screenshot that prompted this: 286 candidates → 2 armed → 2 filled, 50 % WR,
+0.45R, verdict `n too small`. Two trades is not a test of anything; that is exactly what the
`VERDICT` row is for. To get a sample that can be judged, widen the window (15m, or 5m over several
sessions via deeper history) rather than loosening a gate to manufacture trades.
