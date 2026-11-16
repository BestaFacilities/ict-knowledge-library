// NOT PINE CODE — comparison for the user's SNM+ 3.47 script (André Wonou); its exact source is still in chat, not yet checked in as tools/snm-plus.pine.

# SNM+ 3.47 ← CISD Model+ | Authrain Trades: integration study

**Status:** review only. No donor feature has been integrated, and the user's SNM+ is not yet a repository file. Its pasted source is the baseline, not `tools/archive/legacy-indicators/cisd-ultimate-balanced.pine`. Implement original SNM+-style code from observable behaviour, not a wholesale donor-code transplant. Preserve the user's C/RB/RV, Sweep+CISD, A++/A+/A/B, preview, news/session, management, and D/T/E semantics.

## Feature triage

| Donor feature | SNM+ 3.47 already has | Candidate action |
|---|---|---|
| CISD shift defined by persistent opposite-leg *open* and a close through it; potential level before confirmation | `f_cisd` finds the open of the run that made the extreme; Sweep+CISD only after a recent key sweep; ARMED/FORMING previews | **Optional alternate CISD confirmation.** Compare event bars with SNM+'s rule before selecting a default. Require confirmed closes; keep the sweep+NY-AM rule distinct. No retroactive changes to existing tags. |
| HTF CISD detection and near-price merging of chart/HTF confirmations | HTF *candles* and C2/C3 closures, but no drawn HTF CISD registry | **Optional confluence/drawing.** Use last-closed HTF bars, deduplicate same TF and event, merge only labels (never silently remove the other event); preserve object limits. Auto TF map with manual override. |
| Suppress same-direction CISD levels within 0.75 ATR | SNM+ has a per-sweep inversion rank and setup cap, but no price-based dedup | **Optional dedup** for near-identical confirmations, after model/sweep identity check; otherwise two genuinely separate setups could be hidden. Default off until paired-chart review. |
| Hide invalidated CISDs after SL violated | SNM+ has stop lines and optional outcome tracking; previous setups retained with history | **Optional 'dim invalidated / hide invalidated' display mode**, with distinct wick-stop and close-stop semantics and a historical event counter; never erase backtest facts. |
| Automatic liquidity and HTF FVG timeframe selection | SNM+ auto-pairs its TTrades HTF candle but gap slots are fixed 5m/15m/1H/4H | **Optional Auto/Manual gap ladder**, default preserving SNM+'s existing slots; recompute only on chart-TF change. The donor's 1m ladder (15m/1H/D) is *not* SNM+'s current ladder. |
| SMT sensitivity (2/5/10), optional unconfirmed realtime drawing, manual/auto pair | SNM+ pairs index futures automatically and has SMT/PSP and ES gap checks | **Optional sensitivity and manual symbol override**; realtime SMT must be visually provisional and never score confirmed confluence until pivot confirmation. Respect symbol roots/exchange mapping (especially MNQ/MES); no guessed pair on XAUUSD. |
| Configurable alert windows and potential-vs-confirmed alerts | SNM+ has ARMED/FORMING/REJECTED and confirmed alerts; windows and news already gate them | **Add opt-in alert category/window controls** without changing the existing alert stream by default; no news alerts. Avoid duplicate alerts per realtime bar. |
| Normalized six-row checklist grade + watermark | SNM+ has D/T/E, 4-point confluence and an A++/A+/A/B grade | **Do not import the donor grading or watermark.** Optionally expose a compact per-check explanation in the existing panel/tooltip. Keep enabled-check toggles from inflating grades. |
| CTF FVG delivery as origin when no sweep | SNM+ requires a sweep for its setup state | **Experimental toggle only**. This changes the model, not just its display, and needs separate grade/tag (not a silent R or C). |
| Session and swing liquidity; HTF FVG boxes; sizing/targets; simple sweep/SMT drawings | SNM+ already has richer named levels, HRL handling, sponsored 5m gaps, draw/BE/TP2, cross-market checks | **No duplicate subsystem.** A second independent registry would consume objects and give conflicting prices. |

## Donor defects / ambiguities not to carry across

1. `validLongOrigin` / `validShortOrigin` compute an `smt` flag but return `ok = swept or fvg`, so **SMT alone never qualifies** despite the `Detect CISDs from SMTs` tooltip. A port must decide this explicitly and test SMT-only origin. It must not silently bypass SNM+'s key-sweep rule.
2. `addFvg` is gated by `i_showHtfFvg`; turning off HTF gap *drawing* also turns off the FVG registry that grades HTF PDA delivery. In SNM+, display and calculation must remain independent.
3. `gradeSetup` divides by the number of *enabled* checklist rows. Disabling a failing row can increase the grade. SNM+'s grade must not improve merely because a display row is hidden.
4. `g_barTimes` appends every bar without a cap while `cm_legExtremeCurrent/Previous` scan up to 500 bars. Avoid this unbounded history and repeated work; cap every registry and verify counts at several history lengths.
5. The donor's `resolvePair()` uses literal `syminfo.ticker` cases but lacks MNQ/MES and other broker-specific roots; it falls back to a hard-coded ES symbol. Preserve SNM+'s pair behaviour and make unknown symbols explicitly manual/unavailable.
6. `i_hideInvalid` is based on a **close beyond the stop** (`close < slPrice` / `close > slPrice`) although the tooltip calls the SL *violated*. Treat intrabar wick through the stop and close through the stop as distinct configurable events; do not rewrite historical setup labels as if both mean the same thing.
7. Confirmed alert text uses `newBullCisd ? close : close` for "Level"; that's the close, not the actual CISD level. If adopting alert customization, use the event's real trigger level and side/grade captured on the event bar.
8. HTF FVG security requests use historical offsets with `lookahead_off`, but HTF CISD returns live HTF values and the realtime SMT intentionally trails intrabar. Confirmed, provisional and historical values must be visibly distinct; test historical/replay/realtime equivalence before claiming non-repainting.
9. SNM+'s header says “no daily limits, no trade tracking,” yet its optional `iTrack` runs outcomes and a 2-trade/2-loss count when enabled. In the future guide label that feature honestly, but don't change its default-off behaviour as part of this feature comparison.

## Proposed implementation sequence (after the exact SNM+ file is attached)

1. Baseline preservation: save the exact upload as `tools/archive/snm-plus-3.47.pristine.txt` and its SHA-256. The pasted source has comments *before* `//@version=6`; create `tools/snm-plus.pine` by moving only that directive to literal line 1 (required for shipped scripts), record that one-line relocation in the guide, then compile and run initial gates. Do not claim the two files have identical hashes. Pin a *no new feature* benchmark.
2. Add optional, independent utility changes: timeframe auto/manual selection; alert categories/windows; manual correlated symbol + SMT sensitivity. Update the SNM+ settings guide/matrix in the same commit; test that turning display off does not turn computation off.
3. Add optional invalidation/proximity *display* controls, with positive-fire tests for both and preserved historical event records. Verify the default picture matches baseline.
4. Add optional alternate CISD/HTF CISD confluence behind separate toggles and distinct tags. Test close-only confirmation, expiry, dedup, replays and MTF last-closed values. The CTF-FVG-without-sweep route remains experimental and default off pending side-by-side examples.
5. Compare on matched SNM+/reference screenshots for MNQ 1m/3m and another instrument; only then consider changing any default. Document differences by pair and timeframe without requiring manual retuning on every chart switch.

**Verification standard:** real Pine v6 compiler + repository AST validator with a must-fire positive control; runtime harness exercises that assert new code paths actually fire rather than merely compile. A synthetic runtime cannot certify the trading model or a TradingView live-bar picture. At this review stage **none of those checks have run on SNM+ or on the donor**, because neither pasted script exists as a workspace file.
