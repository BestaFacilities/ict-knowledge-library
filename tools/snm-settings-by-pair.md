// NOT PINE CODE — maintained settings guidance for tools/snm-plus.pine (SNM+ 3.52).

# SNM+ 3.52: pair / timeframe / session settings

Update this file in the **same commit** as any new input, changed default, or renamed group in `tools/snm-plus.pine`. All times below are New York time (DST handled by Pine's `America/New_York`). This is setup display guidance, not investment advice or a performance claim.

| Symbol on chart | SMT sibling (`Auto`) | Default point-based fallbacks | Notes |
|---|---|---|---|
| NQ | ES | EQ tolerance 3 pt; max stop 75 pt; Judas candle 25 pt; edging 50 pt | Keep Auto pair. |
| MNQ | MES | Same NQ fallbacks | Keep Auto pair; the SNM+ risk sizing uses `syminfo.pointvalue`, not the symbol name. |
| ES | NQ | EQ tolerance 0.75 pt; max stop 18 pt; Judas candle 6 pt; edging 12 pt | Keep Auto pair. |
| MES | MNQ | Same ES fallbacks | Keep Auto pair. |
| XAUUSD / other | none | EQ fallback 4 ticks; edging fallback 50 ticks; no auto max-stop/Judas point threshold | Do not assume ES is the correlated feed. Manual SMT symbol only after confirming data and directionality on your broker's chart. |

These are the script's **existing auto defaults**, not new parameter recommendations. Manual values of 0 in those inputs mean Auto, except `iGapMin` which is a multiple of ATR. Do not copy MNQ point distances into gold.

| Entry chart TF | TTrades HTF with `Fractal pairing = Auto` | Chart iFVG + optional higher inversions | HTF delivery: Fixed (default) → Auto (opt-in) |
|---|---|---|---|
| 1m | 15m | 1m, 2m, 3m, 5m | 5m sponsored + **15m / 1H / 4H** → same |
| 3m | 30m | 3m, 5m | same → same |
| 5m | 1H | 5m | 5m sponsored + **15m / 1H / 4H** → **1H / 4H / 1D** |
| 15m | 4H | 15m | same Fixed slots (15m duplicates the chart TF) → **1H / 4H / 1D** |
| 30m–1H | 4H | chart TF | Fixed stays 15m/1H/4H → Auto selects **4H / 1D / 1W** (only slots above chart TF are admitted) |

`HTF gap timeframe mode = Fixed` reproduces the 3.48 calculation and delivery. In Fixed, `Fixed gap TF 1 / 2 / 3` default to 15/60/240; choose distinct TFs above the chart if overriding. Auto is a deliberate new **signal-context** choice, not just display: FVG delivery and target availability can change. No settings edits are needed *between* chart timeframes once Auto is chosen; choose it once and compare with Fixed in replay.

**Diagnostics for a missed MNQ 1m short (3.52, off by default):** on the same broker feed and replay date, enable `Show iFVG near-miss reasons` once and hover amber `?` around 04:35–04:40 NY. The tool reports confirmed gap-close failures, small raw chart gaps, and model/grade gates, but not wick-only reactions or raw gaps on 2m/3m/5m that never made the registry. It never grants a trade, removes the key-sweep rule, or overrides the manual bias. Keep the normal gap timeframe pairing (Fixed or Auto) when switching chart TF; diagnostics need no TF-specific tuning. Turn the study mode back Off when done.

**HTF gap lifecycle (3.51 default change):** `HTF FVG invalidation = Hybrid (HTF close)` follows each strictly higher slot TF automatically: 1H gaps await a confirmed 1H close, 15m gaps a 15m close, and so on. A chart-TF close beyond the far edge immediately marks the zone **BREACHED** (grey dashed, no delivery/target/sponsorship/edging/map credit), rather than deleting it; a confirmed source-TF close beyond deletes it, or a confirmed reclaim reactivates it for *future* setups. A manual Fixed slot at/below the chart TF and standalone sponsored 5m gaps still invalidate on chart close. `Also the gaps price is trading inside` defaults **On** (display only), making near-price gaps visible without manual TF-specific retuning. To restore **3.50**, set `HTF FVG invalidation = Chart close (3.50)` and `Also the gaps price is trading inside = Off`. Prefer matching broker/symbol/replay time when comparing, because a box is not proof of delivery.

**HTF CISD context (new 3.50, off by default):** set `Enable confirmed HTF CISD context = On` once; `HTF CISD timeframes = Auto` then picks 2m/3m on 1m, 5m/15m on 3m, 15m/30m on 5m, 1H/4H on 15m, 4H/1D on 1H. The chart and lower TFs are skipped. The 60-minute freshness window starts at the confirmed HTF candle's actual close (also across market gaps); it is wall-clock minutes, **not 60 chart bars**. `Draw confirmed HTF CISD lines` can be switched off independently without disabling the tooltip read. The 4-line cap is global. No change to entry eligibility, grade or alerts; on XAUUSD this is the same chart symbol's HTF candle-leg context, unrelated to the SMT sibling. If you choose Manual, use two distinct TFs above your entry chart.

**Session defaults:** Asia 20:00–00:00; London 02:00–05:00; Premarket 08:00–09:30; NY AM 09:30–11:00. Trading windows: Asia/London/NY AM. Judas: 09:30–09:45. Macro windows: 09:50–10:10 and 10:50–11:10. Automatic NFP blackout approximates first Friday 08:30 NY (check actual release date); type other red-folder dates in `Other releases` each week. The optional alert windows narrow, never widen, the original trading/news window gate.

**Default differences from uploaded 3.47:** the new 3.52 diagnostic defaults Off; 3.51 uses Hybrid gap invalidation and shows gaps containing price; a reclaimed HTF gap can qualify only *after its own confirmed close*. Setup grade/draw/targets therefore may differ from 3.47 or 3.50; compare in replay before relying on this default. Earlier 3.48–3.50 additions kept their original defaults. New dedup defaults **off**, sibling mode **Auto**, alert master/categories **on**, separate alert windows **off**, `HTF gap timeframe mode` defaults **Fixed**, `Drawings after stop` defaults **Keep**, and `Stop touch means` defaults **Wick** (inactive while Keep), and `Enable confirmed HTF CISD context` defaults **Off** (its Auto TF map and drawing defaults are inactive until on). Manual sibling defaults to ES but is inactive in Auto. The sole non-optional safety fix: a configured but unavailable SMT sibling no longer counts as valid correlation data. For a control run, leave every new toggle at its default and compare the same symbol, same broker, same timeframe and date in TradingView; only turn one new control on at a time.
