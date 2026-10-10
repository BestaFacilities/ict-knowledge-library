// NOT PINE CODE — this is a markdown guide. Do not paste it into the Pine Editor.
// The script it documents is: tools/archive/mx-context-overlay.pine  (that file is the code).
// The trigger/journal side is documented in tools/archive/cisd-v2-guide.md.

# MX Context Overlay (build 1.1) — what the panel means, and the four settings that matter

## 1. What it is

A **reading layer**. It places no levels, sizes nothing, and alerts on nothing — that is
`cisd-ultimate-proper-v2.pine`'s job. This script answers the other four questions, in the
vocabulary a ManipulationX-style read uses:

- which HTF array is holding under price, and which timeframe it came from;
- what the session has already taken (data-window extremes, the 9:30 wick, pooled equal highs/lows);
- whether the sibling index confirmed the extreme (SMT);
- how much stands between here and the next draw on liquidity (the runway).

Every block in the file names the concept page it implements, so a claim can be checked rather than
trusted. The feature inventory and the reasoning for keeping it a **separate script** instead of
folding it into v2 is in `tools/mx-setups-study.md`.

## 2. Four settings, not twenty

| setting | what it does |
|---|---|
| **Density** (`Minimal` / `Normal` / `Full`) | how much is drawn: 1 / 2 / 4 arrays and pools per side, session lines off/on/on, premium-discount shading only at `Full`, box span 60 / 150 / 320 bars. |
| **Higher timeframe 1–3** | which timeframes count as higher. Blank disables a slot; a slot equal to the chart timeframe is skipped. |
| **Min array height (chart ATR)** | the single knob that decides empty chart versus wall. Measured in *this chart's* ATR, so raising it filters small timeframes harder. |
| **Sibling symbol** (+ `SMT` on/off) | needs a data entitlement for that symbol. Without one the checkpoint is not counted — see §4. |

Everything else is a model parameter (window hours, pivot length, near-equal tolerance, expiry). The
per-side draw counts, the registry memory bounds and the panel contents are **not** inputs any more:
they were seven knobs whose only effect was to be set wrong.

## 3. The panel (bottom right, 4 columns × 7 rows)

Two checkpoints per row. Every cell has a tooltip; the tooltip carries the citation.

| row | left | right |
|---|---|---|
| 0 | `Bias` — sum of four independent statements (HTF, arrays, pools, session position) | `Passed n/6 · grade` |
| 1 | header | header |
| 2 | **FVG delivery** — did the leg leave an array standing behind it | **Reacting from array** — price is trading *out of* one, not merely near one |
| 3 | **AMD / Judas run** — pre-open extreme taken and reclaimed inside the window | **SMT confirm** — `off` / `no data` / ✓ / ✗ |
| 4 | **Half of the range** — long below 0.5, short above, with the % printed | **Pool ahead** — nearest standing pool with enough touches |
| 5 | **Low-resistance runway** — obstacles between here and that draw | **Arrays standing** — registry size after this bar's mitigation and expiry |
| 6 | `Defects` | the named (bad) bullets, comma-separated |

Colour = bias, not conviction. A green row means that checkpoint passed, nothing more.

## 4. `Passed n/6` is a real denominator

Six checkpoints always count; SMT counts only when it is on **and** the sibling returned data. A
disabled test is neither a pass nor a defect — it is excluded from the numerator and the denominator.

This matters because the previous build did the opposite: a disabled SMT awarded a point, and a chart
with no FVG delivery, no pools and no sibling data still printed `5/7 · A-`. If you see a grade that
contradicts the `Defects` row, the Defects row is the one to believe, and the grade string is
`A+ / A / A- / B+ / C` cut at fractions of *enabled* checkpoints (1.0 / 0.85 / 0.70 / 0.55).

The grade is a legibility aid for a read you already made. It is not a signal — see study §4.

## 5. Presets

Density replaces the old draw-count knobs, so a preset is four numbers now:

| chart | HTF 1 / 2 / 3 | Min array height | Array expiry | Pivot length | Sibling | Density |
|---|---|---|---|---|---|---|
| NQ 5m | 240 / 60 / 15 | 0.15 | 400 | 6 | `ES1!` | Normal |
| NQ 15m | 480 / 240 / 60 | 0.25 | 200 | 6 | `ES1!` | Normal |
| XAUUSD 60m | `D` / 240 / 60 | 0.15 | 120 | 8 | `DX-Y.NYB` | Normal |
| NAS100 240m | blank / blank / `D` | 0.40 | 60 | 4 | `ES1!` | Minimal |
| XAUUSD 5m (what the screenshot was) | 240 / 60 / 15 | 0.35 | 240 | 6 | blank | **Minimal** |

Gold on 5m is the densest case in the set: 286 candidates in 150 bars, gaps on every timeframe. If
the chart is a wall at `Minimal`, raise `Min array height` before touching anything else.

## 6. Ten-minute triage, in order

1. **Delete both indicator instances and re-add them.** TradingView caches the compiled build per
   script name; the legend must read `MX Context` and `CISD v2` with the build tags in the title.
2. The clock row (v2's panel) reads out of hours on a broker-timezone chart — set the session
   timezone input, don't infer from the axis.
3. No FVG box at all while price sits in an obvious gap → the height filter, not the market. Lower
   `Min array height` to 0 and see whether boxes appear; then walk it back up.
4. `Arrays standing` = 0 with boxes visible → they were all run through. That is the delete-on-spend
   behaviour working: an inverted array is history, not a draw.
5. `Defects` says `no pool ahead` on a chart with obvious equal highs → raise `Swing pivot length`
   to 8 and `Touches to make a pool` stays at 2. Pools are built from confirmed pivots, so they lag
   by that many bars by construction.
6. SMT reads `no data` → you do not have a subscription for the sibling. Turn the input off; the row
   then says `off` and the denominator drops to 6 either way.

## 7. What build 1.1 changed, and what it cost

| | before | after |
|---|---|---|
| inputs | 34 (7 of them visual micro-knobs) | 28 (Density absorbs them) |
| registry scans per bar | 2 (scoring scan, then a drawing scan) | 1 |
| spent arrays | kept, redrawn as `inv` boxes with a creation-time left edge → multi-hundred-bar walls | deleted, counted in `inverted` (row 2's tooltip) |
| drawn box width | unbounded | clamped to 60 / 150 / 320 bars |
| panel | 2 × 11, `position.top_right` — **underneath v2's dashboard** | 4 × 7, `position.bottom_right` |
| grade | divided by 7 always | divided by the enabled count |
| script time, 1200 synthetic bars, same shims | 854 / 823 ms | 683 / 684 ms (−20 %) |

The timing pair was produced with `python3 tools/pine-gate-run.py` (§12 of
`tools/cisd-audit.md` has the conditions and the caveats). The runtime is not a signal oracle: the
bars are synthetic and contiguous, so the numbers there are about the *plumbing*, not the model.

## 8. Limits, stated

- The data window is a **clock**, not a calendar. It knows 8:30–9:30 exists; it does not know a print
  happened. Nothing in Pine can read an economic calendar.
- Pivots confirm `poolLen` bars late, so a pool's label can trail the touch count by that many bars.
- HTF arrays appear on the bar whose close completed them — the same delay as any `request.security`
  layer that does not repaint.
- `SMT` compares pivots of the two series, which aligns them by construction but cannot detect a
  data gap on the sibling: if the sibling returns nothing, the row says so rather than guessing.
