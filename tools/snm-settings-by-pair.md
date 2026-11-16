// NOT PINE CODE — maintained settings guidance for tools/snm-plus.pine (SNM+ 3.48).

# SNM+ 3.48: pair / timeframe / session settings

Update this file in the **same commit** as any new input, changed default, or renamed group in `tools/snm-plus.pine`. All times below are New York time (DST handled by Pine's `America/New_York`). This is setup display guidance, not investment advice or a performance claim.

| Symbol on chart | SMT sibling (`Auto`) | Default point-based fallbacks | Notes |
|---|---|---|---|
| NQ | ES | EQ tolerance 3 pt; max stop 75 pt; Judas candle 25 pt; edging 50 pt | Keep Auto pair. |
| MNQ | MES | Same NQ fallbacks | Keep Auto pair; the SNM+ risk sizing uses `syminfo.pointvalue`, not the symbol name. |
| ES | NQ | EQ tolerance 0.75 pt; max stop 18 pt; Judas candle 6 pt; edging 12 pt | Keep Auto pair. |
| MES | MNQ | Same ES fallbacks | Keep Auto pair. |
| XAUUSD / other | none | EQ fallback 4 ticks; edging fallback 50 ticks; no auto max-stop/Judas point threshold | Do not assume ES is the correlated feed. Manual SMT symbol only after confirming data and directionality on your broker's chart. |

These are the script's **existing auto defaults**, not new parameter recommendations. Manual values of 0 in those inputs mean Auto, except `iGapMin` which is a multiple of ATR. Do not copy MNQ point distances into gold.

| Entry chart TF | TTrades HTF with `Fractal pairing = Auto` | Chart iFVG + optional higher inversions | Existing HTF delivery slots |
|---|---|---|---|
| 1m | 15m | 1m, 2m, 3m, 5m | 5m sponsored, 15m, 1H, 4H |
| 3m | 30m | 3m, 5m | same |
| 5m | 1H | 5m | same (some slots equal the chart TF; turn off duplicated drawings if they clutter, but no manual retuning is required to switch) |
| 15m | 4H | 15m | same; 15m slot is the chart's own gap, so review whether it adds information. An automatic gap ladder is still planned. |

**Session defaults:** Asia 20:00–00:00; London 02:00–05:00; Premarket 08:00–09:30; NY AM 09:30–11:00. Trading windows: Asia/London/NY AM. Judas: 09:30–09:45. Macro windows: 09:50–10:10 and 10:50–11:10. Automatic NFP blackout approximates first Friday 08:30 NY (check actual release date); type other red-folder dates in `Other releases` each week. The optional alert windows narrow, never widen, the original trading/news window gate.

**Default differences from uploaded 3.47:** none in signal qualification, tag style, fixed HTF gap slots, or alert times. New dedup defaults **off**, sibling mode **Auto**, alert master/categories **on**, separate alert windows **off**. Manual sibling defaults to ES but is inactive in Auto. The sole non-optional safety fix: a configured but unavailable SMT sibling no longer counts as valid correlation data. For a control run, leave every new toggle at its default and compare the same symbol, same broker, same timeframe and date in TradingView; only turn one new control on at a time.
