// NOT PINE CODE — usage guide for tools/snm-plus.pine (SNM+ 3.48); paste the .pine file, not this guide, into TradingView.

# SNM+ 3.48 — first integration pass

**Current source:** `tools/snm-plus.pine`. The author's exact uploaded 3.47 baseline (before any edits) is `tools/archive/snm-plus-3.47.pristine.txt`, SHA-256 `abbc9ffda5c39c2176b4695d4abc0096aa996d04a5d0e6787d94971815ea0b96`. The uploaded file began with comments; only the working version moves `//@version=6` to literal line 1. The working version was renamed 3.48 so TradingView cannot silently show a stale 3.47 instance. Remove the old instance, paste the new code, save and re-add it.

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

No new input changes the default signal pipeline. The only baseline cleanup is spelling out 12 previously omitted default function arguments, so the AST validator no longer falsely marks them as arity errors. The working title/header were bumped to 3.48. SMT now additionally checks that the configured sibling has actual high/low data; an invalid manual symbol cannot award a false confirmation.

## Pair and timeframe

See `tools/snm-settings-by-pair.md` for the maintained profile. `SMT sibling = Auto` and `Fractal pairing (HTF candle) = Auto` require **no manual changes when switching between 1m, 3m, 5m and 15m** on index futures. `Structure timeframe (C / R) = 15m` and HTF FVG slots remain the 3.47 defaults; a separate optional Auto/Manual *gap-ladder* is planned, not yet implemented. On XAUUSD, Auto has no NQ/ES sibling, so leave SMT off or use Manual with a real correlation feed and review it chart-side. `Bias (your IF/THEN)` remains a morning manual choice by its original design, not a timeframe setting.

## What we did *not* import from CISD Model+

Its separate CISD flip state machine, HTF CISD drawings/merging, invalidated-line mode, real-time SMT and current-timeframe-FVG-without-sweep are **not in this build**. They would change what qualifies as a setup, draw unconfirmed information, or consume additional object budget. They remain described as opt-in follow-up work in `tools/snm-integration-plan.md`, not falsely advertised as shipped. We also did not import its A+/A/B-/C grading, which conflicts with SNM+'s DTE rulebook.

## Verification and limits

- Pristine upload SHA-256 matches the attached file. The normalized 3.47 working copy passed the v6 checker (0 errors, 22 existing warnings) and pyne parser; pyne raw 400-bar synthetic run returned successfully. After this pass, repeat the compiler and AST checks on 3.48 before sharing it.
- `tools/pine-validate.py --selftest` fires both its fixture and its real-control defect. `tools/pine-validate.py tools/snm-plus.pine` must be CLEAN; `tools/pine-lint.sh tools/snm-plus.pine` must have zero errors. These checks are not a TradingView chart rendering test.
- **Runtime gate limitation:** hoox-pyne runs this SNM+ source in *object* mode but returns `plots: {}` even for explicitly appended numeric probes, and reports only the initial global `bgcolor` in `extras`. The SNM+ exercise in `pine-gate-run.py` deliberately reports `PROBLEM` (it cannot observe a positive-fire verdict). We will not call that a passing gate. Verify duplicate suppression, pair-feed availability and alert routing on TradingView replay/live before trusting those switches; compare toggles off against the pristine 3.47 in the same chart/window. In particular, the original ARMED/FORMING alerts use `alert.freq_all` with `var` latches; whether they repeat intrabar is not verified here.
