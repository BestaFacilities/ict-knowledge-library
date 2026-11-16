# ManipulationX V.8 replica — how to use it

// The script this guide belongs to is **tools/mx-replica.pine** (paste that file into
// TradingView's Pine editor). It is original code written to match the *observable behaviour*
// of a private, invite-only indicator. Nothing from that script could be read — it is not
// viewable — so what follows is honest about which parts are observed and which are inferred.
// If a future version of the original shows different behaviour, this file gets corrected, not
// defended.

## What you get

- Green **C** tags (continuations) and **R** tags (reversals), on the same tags the original
  draws: **C** below/above for longs/shorts in trend context, **R** at swept extremes.
- The context the original surrounds them with, so the tags read in a chart that already makes
  sense: sweep-to-dashed liquidity levels (`SSS` = a swept pool), resting solid levels, iFVG
  boxes, two higher-timeframe FVG slots, Asia/London/NY session extremes, EQH/EQL, LRL lines,
  SMT lines, and the bottom-right checklist panel (`Bias`, then Macro / Liquidity Sweep /
  HTF Delivery / Volume / Session DOL / LTF DOL / V-Shape / SMT with ✓/✗).

## The signal this replica actually takes

Three gates, in order — the original's own mechanism, and deliberately nothing else:

1. **Sweep.** Price wicks through a resting BSL/SSL level (a Length-20 pivot line) and closes
   back. The level turns dashed, gets an `SSS` tag, and a 30-bar window opens (`Sweep stays
   valid for`). If the sweep never comes, a later inversion can still print **C** — never R.
2. **Inversion.** The signal bar is a close through a resting chart-timeframe FVG — the
   inverse-FVG confirmation. Every counter-trend FVG born inside the sweep leg must also have
   inverted first (`All iFVGs In Leg Must Inverse`, default on, from their panel by name).
3. **Classify.** Inversion inside the sweep window → **R**. Otherwise **C**, if the inversion
   agrees with the bias (or the bias is Neutral). Filters (Volume, Session DOL, V-Shape, SMT)
   hide tags whose conditions fail; they never change the first two gates. Killzones do not
   gate signals by default — see `Require Signals Inside a Killzone` below for why.

## Settings, per the pairs you run

The point of this indicator on your desk is that you should not retune it by hand when you
switch symbol or timeframe, so the defaults below are set once, per symbol class, and the
timeframe behaviour is derived rather than typed in.

| | MNQ | XAUUSD |
|---|---|---|
| `SMT symbol` | `TVC:DXY` (their NQ charts read “SMT w/ DXY”) | your broker's DXY (`TVC:DXY` or `FOREXCOM:DXY`) |
| `EQ Max Difference` | **1.0** | **1.0** — note this is *points*: their `0.15` was on MNQ, where one tick is 0.25 |
| `Minimum Size` | 1.0 | 0.5 |
| Killzones | New York 09:30–11:00, London 02:30–04:00 | same |
| Day-type context | Asia H/L, London H/L, 8AM/9AM candle ranges | same |

Per timeframe, on either symbol: **3m is the intended signal timeframe**, **1m for the precise
entry** (the original's own two widths in your set). The HTF FVG slots default to **15-minute
and 1-hour delivery** on 1m and 3m alike; if you run the replica on a 15m chart, cut the two
slots to **1H and 4H** or you are plotting the chart's own gaps twice.

## Deliberate deviations, all one toggle from the original's look

- **Killzones don't gate signals** (`Require Signals Inside a Killzone`, default off). Their
  own tags on your charts print two minutes outside their London window — a hard gate is a
  behaviour your screenshots rule out. Turning this on makes signals window-only.
- **Bias** (`Daily Bias (checklist direction)` — Auto / Bullish / Bearish / Neutral): the
  panel's Bias reads different on your 3m than your 1m at the same clock moment, so it cannot
  be only the manual dropdown; Auto reads it from the last Length-20 pivot range the close
  broke on the chart's own timeframe. Picking Bullish/Bearish/Neutral overrides it.
- **A+ Reversals** still prints every R; `Show A+ Reversals Only` hides the ones whose
  eight-row checklist scores under 6 (`A+ Minimum Checklist Score`). This is the literal
  reading of the name — see *Inferred* below.
- `Use Ez Killzones` draws the simple session boxes (their default-off look). Default matches
  their grey shaded sessions on your 1m set.

## Inferred — what could not be observed from the screenshots

Stated even where it is probably right, because "probably right" is the thing this file exists
not to dress up as observed:

- **Bias construction** (above). The dropdown exists in their panel; the per-timeframe split is
  real; the pivot-break rule is our reading of it, not their code.
- **A+** = checklist score ≥ 6. Unobservable from a still screenshot.
- **`Internal Liquidity`**: their two HTF FVG slots with text and wick mitigation match the
  observed boxes exactly (`15M FVG-` above price, `15M FVG+` below); whether their zones do more
  than hold mitigation is not observable.
- **Session DOL / LTF DOL** checklist rows read: an *untaken* session level still beyond price
  (Session DOL), a *resting* LTF pool still beyond price (LTF DOL). The user's own study had
  these as targets, not signals — they remain checklist and (optionally) filter only.
- **LRL** lines step through consecutive same-direction pivots; the original's exact spacing
  rule is not observable from stills.

## Verification

- `tools/pine-validate.py` (AST rules, positive control checked): **CLEAN**.
- `tools/pine-lint.sh` (real v6 compiler): **0 errors**; 39 checker warnings of one class —
  the tuple-reassignment idiom the compiler accepts and this repo's other scripts avoid.
- `tools/pine-gate-run.py tools/mx-replica.pine` under the reference runtime: the engine
  exercise fires the whole chain (sweeps=402, inversions=798, sigR=402, sigC=396) with caps
  held (levels=10, gaps=24 resting, htf=12). That verifies the *code paths*, with synthetic
  pivots and gap geometry substituted as the harness documents — it is not evidence about real
  win rates, and SMT on that run is the chart compared with itself, so it proves the comparison
  code runs, not that divergence does.

**Next step that would actually improve it:** add the replica alongside the original on one
instrument for a few sessions and note any Bar where one prints and the other doesn't — that
difference Bar is worth more than any setting.
