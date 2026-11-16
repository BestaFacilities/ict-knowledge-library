// NOT PINE CODE — usage guide for tools/snm-plus.pine (SNM+ 3.50); paste the .pine file, not this guide, into TradingView.

# SNM+ 3.50 — optional confirmed HTF CISD context

**Current source:** `tools/snm-plus.pine`. The author's exact uploaded 3.47 baseline (before any edits) is `tools/archive/snm-plus-3.47.pristine.txt`, SHA-256 `abbc9ffda5c39c2176b4695d4abc0096aa996d04a5d0e6787d94971815ea0b96`. The uploaded file began with comments; only the working version moves `//@version=6` to literal line 1. The working version is named and short-titled **SNM+ 3.50** so the chart legend can distinguish it from your old instance.

## Install it first — it is not published in TradingView

This repository file does **not** install itself into TradingView. The GitHub default branch (`master`) also does not contain it yet; the file is on branch `arena/1ccc44fe-ict-knowledge-library`.

1. Open `tools/snm-plus.pine` in the workspace viewer, or on GitHub select that branch and open `tools/snm-plus.pine` (not the archived `.txt`). Copy the **entire file**, beginning with `//@version=6`.
2. In TradingView open a chart → **Pine Editor** (bottom tab) → **New / Blank indicator**. Select all the placeholder code, paste 3.50, click **Save** (name it `SNM+ 3.50`), then **Add to chart**.
3. Remove the older SNM+ 3.47 indicator instance from the chart to avoid overlapping drawings. The chart legend should say **SNM+ 3.50**. Only then open its **gear → Inputs** for the new settings below. If the legend says `SNM+ 3.49`, `SNM+ 3.48` or just `SNM+`, you are still looking at an older build.
4. If TradingView reports a compiler or resource error, send the exact message and line number before trusting any chart output. This repo's checker is not TradingView's server compiler.

## What the core still does

SNM+ **draws setups, not trades**. It tracks named and intraday swing sweeps, uses an iFVG inversion or the optional Sweep + CISD close as trigger, and classifies C / RB / RV from 15m structure. A++/A+/A/B, the D/T/E checklist, HTF FVG delivery, HRL avoidance, BE/TP1/TP2, NY-time windows, news dimming and ARMED/FORMING previews remain the original design. A++ still requires premarket + macro reversal context. `Auto outcome (backtest)` remains **off by default**; when switched on, its mechanical tally counts at most two qualifying setups/two losses per day. This is a study tool, not an order-placement strategy. An active preview can change before the candle closes; wait for the confirmed tag.

## New controls (all default to the 3.47 behaviour)

| Group / setting | Default | Effect |
|---|---|---|
| Setup → Suppress near-duplicate confirmations | **Off** | When on, suppress a *second rendered setup* from the same sweep, model and direction if its trigger is closer than `Dedup trigger distance (x ATR)` over `Dedup lookback (bars)`. A genuinely new sweep can print at the same price. The prior tag is not removed. |
| Setup → Dedup trigger distance (x ATR) | 0.75 | Price spacing for the optional suppressor, only when that toggle is on. |
| Setup → Dedup lookback (bars) | 15 | Age window for the optional suppressor, only when that toggle is on. |
| Confluence → SMT sibling | **Auto** | Keep the exact original NQ↔ES and MNQ↔MES root pairing. `Manual` uses the symbol chosen below; helpful on a broker-specific feed or a different instrument. |
| Confluence → Manual SMT symbol | `CME_MINI:ES1!` | Inactive in Auto. Set to a *valid feed on your account* in Manual; if the series is unavailable, SMT/PSP/ES confirmations must not be counted as true. It does **not** create an alternative on its own when SMT is off. |
| Alerts → Enable alerts | **On** | Master switch for the existing `alert()` calls. Does not turn drawings or grading off. |
| Alerts → Confirmed / Armed–forming / Rejected | **On / On / On** | Independent switches on the existing categories. No news blackout alert is added. |
| Alerts → Use separate alert windows (NY) | **Off** | Off means the original trading-window alert behaviour. On means an alert also needs to fall in window 1 (09:30–11:00) or optional window 2 (02:00–05:00, default off). All hours are New York time; windows *intersect* rather than replace the trading windows and the news blackout. |
| Confluence → HTF gap timeframe mode | **Fixed** | `Fixed` = the original gap slot TFs 15m / 1H / 4H. `Auto` chooses 15m / 1H / 4H on a 1m or 3m chart, 1H / 4H / 1D on 5m or 15m, 4H / 1D / 1W on 30m or 1H; slots at or below the chart TF are skipped in Auto. **Auto can change delivery, draws and grades**, so compare it on replay before relying on it. |
| Confluence → Fixed gap TF 1 / 2 / 3 | 15m / 1H / 4H | Editable only in Fixed mode. Keep them distinct, preferably above the chart TF; if you choose e.g. 45m or 3H, their reversal delivery rank is derived from actual seconds, not the slot number. |
| Confluence → Gap slot 1 / 2 / 3 | **On / On / On** | The previous 15m / 1H / 4H slot toggles renamed to reflect Auto TFs; the 5m sponsored slot is unchanged. Turning a slot off removes its calculation *and* drawing, whereas `Draw HTF gaps` hides boxes only. |
| Display → Drawings after stop | **Keep** | `Dim` recolours the tag, box, lines and labels once price touches the chosen stop on a **later confirmed bar**; `Hide` makes those objects transparent/blank without deleting their IDs (so they still count toward object limits until `Setups kept on the chart` prunes them). This never changes historical setup counts, alerts, grades, or the optional outcome tracker. The last-setup panel can still report that historical setup. |
| Display → Stop touch means | Wick | Used for Dim/Hide only. `Wick` triggers on price touching the stop; `Close` requires a strict close through. Does not change the optional outcome tracker, which remains wick-first. |
| HTF CISD confluence → Enable confirmed HTF CISD context | **Off** | Separate observation layer; detects a candle-leg-open close-through on *closed* HTF bars, then shows a recent same-direction event in a confirmed setup's tooltip. **It does not add entries or change the four-point confluence score, A++/A+/A/B grade, alerts, bias, target, or the existing Sweep + CISD gate.** |
| HTF CISD confluence → Draw confirmed HTF CISD lines | **On (inactive until context is enabled)** | Dotted `2m CISD+` / `3m CISD-` (or selected TF) lines. Turn off for tooltip-only context. Only confirmed events draw; no live-candle potential line is drawn. |
| HTF CISD confluence → HTF CISD timeframes | **Auto** | 1m chart: 2m/3m; 3m: 5m/15m; 5m: 15m/30m; 15m: 1H/4H; 1H: 4H/1D. TFs equal to or below the chart and duplicate slots are skipped. `Manual` uses the two HTF input fields. Auto works across chart timeframes without retuning. |
| HTF CISD confluence → Context valid for (minutes) | 60 | Freshness measured from the confirming HTF candle's *actual close* (usually the next candle's opening, but not across an overnight/weekend gap). Clock units are elapsed minutes measured through the confirming setup bar's close, so changing chart timeframe does not change the window; events already expired at that close are not registered. |
| HTF CISD confluence → Confirmed lines kept total | 4 | Global cap across both TFs and directions; the oldest line/label is deleted on replacement. A previously fresh line remains as historical context after expiry (its extension stops); only the setup tooltip says whether context was fresh. Turning Draw off stores only small metadata, not drawings. |

No new input changes the **default** signal pipeline. The only baseline cleanup is spelling out 12 previously omitted default function arguments, so the AST validator no longer falsely marks them as arity errors. The working title/header are now 3.50. SMT now additionally checks that the configured sibling has actual high/low data; an invalid manual symbol cannot award a false confirmation.

## Pair and timeframe

See `tools/snm-settings-by-pair.md` for the maintained profile. `SMT sibling = Auto`, `Fractal pairing (HTF candle) = Auto`, and the optional `HTF CISD timeframes = Auto` require **no manual changes when switching between 1m, 3m, 5m and 15m** on index futures. `Structure timeframe (C / R) = 15m` and `HTF gap timeframe mode = Fixed` preserve the 3.47 default gap slots; switch the latter to Auto **once** if you want slots to follow chart timeframe automatically, then compare delivery and tags on replay. On XAUUSD, Auto has no NQ/ES sibling, so leave SMT off or use Manual with a real correlation feed and review it chart-side. `Bias (your IF/THEN)` remains a morning manual choice by its original design, not a timeframe setting.

## What we did *not* import from CISD Model+

Its alternate *entry* CISD flip engine, HTF/CTF label merging, real-time SMT and current-timeframe-FVG-without-sweep are **not in this build**. The opt-in HTF CISD layer is context-only, not an additional setup engine. The optional stop-based Dim/Hide display mode is implemented without adopting the donor’s close-only invalidation rule. They would change what qualifies as a setup, draw unconfirmed information, or consume additional object budget. They remain described as opt-in follow-up work in `tools/snm-integration-plan.md`, not falsely advertised as shipped. We also did not import its A+/A/B-/C grading, which conflicts with SNM+'s DTE rulebook.

## Verification and limits

- Pristine upload SHA-256 matches the attached file. The normalized 3.47 working copy passed the v6 checker (0 errors, 22 warnings) and pyne parser; pyne raw 400-bar synthetic run returned successfully. On **3.50**, the open-source Pine v6 checker reports 0 errors (22 warnings), the AST validator reports CLEAN with a firing self-test positive control, and the pyne parser reports OK. This is not TradingView's own server compiler, and these checks do not show that the optional branch fires on real market data.
- `tools/pine-validate.py --selftest` fires both its fixture and its real-control defect. `tools/pine-validate.py tools/snm-plus.pine` must be CLEAN; `tools/pine-lint.sh tools/snm-plus.pine` must have zero errors. These checks are not a TradingView chart rendering test.
- **Runtime gate limitation:** hoox-pyne runs this SNM+ source in *object* mode but returns `plots: {}` even for explicitly appended numeric probes, and reports only the initial global `bgcolor` in `extras`. The SNM+ exercise in `pine-gate-run.py` deliberately reports `PROBLEM` (it cannot observe a positive-fire verdict). We will not call that a passing gate. Verify dedup, pair-feed availability, alert routing, the Auto gap ladder, Dim/Hide, and the confirmed-only HTF CISD layer on TradingView replay/live before trusting those switches; compare toggles off against the pristine 3.47 in the same chart/window. In particular, the original ARMED/FORMING alerts use `alert.freq_all` with `var` latches; whether they repeat intrabar is not verified here.
