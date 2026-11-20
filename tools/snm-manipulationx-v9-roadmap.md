// NOT PINE CODE — planning note for tools/snm-plus.pine (active source: SNM+ 3.69).

# Prioritized ManipulationX V9 → SNM+ roadmap

**Status:** Priority 1 / Stage 1 was implemented as display-only in SNM+ 3.64 and Stage 2 (checklist clarity) in SNM+ 3.65; the Clean/MX Lite views were later removed in 3.68 and the extras (diagnostics, HTF CISD, NWOG, Monday, Judas, 5M HTF zones) in 3.69. The remaining items are recommendations. This roadmap is based on `tools/snm-manipulationx-v9-comparison.md`, the user's 11 screenshots (`image-38.png`–`image-48.png`) and video transcript, and SNM+ 3.63 as the implementation baseline. No V9 code is being ported. Stage 1 does not change setup qualification, C/RB/RV model labels, D/T/E grading, targets, risk management, alerts, session rules, or timeframe behavior.

The screenshots show one saved V9 configuration, not verified factory defaults. In particular, the V9 screenshot and narration disagree about HTF FVG mitigation (50% / wicks versus 100% / close). Treat that donor rule as unresolved. The V9 performance and non-repainting claims are also unverified.

## Recommendation at a glance

1. **Start with SNM+ 3.64's existing Clean view** for a lighter chart; it remains display-only. No new feature is needed to try this.
2. **MX Lite is now available in 3.64** as an opt-in compact display profile with independent setup-tag/trigger-zone visibility and a latest-setup-only drawing option. Current remains the default and Clean remains available.
3. **Checklist clarity is implemented in 3.65:** the panel reuses SNM+'s existing checks and labels **LAST SETUP** separately from **NOW**, with explicit n/a / – states. This is information design, not a new qualification layer.
4. Treat the 8AM/9AM candle ranges and standalone event alerts as **later, separately specified proposals**. Their definitions or alert events are not complete enough to implement safely from the screenshots alone.
5. **Do not import V9 filters, grades, LRL/HRL constructions, mitigation rules, or performance claims as SNM+ behavior.**

## Prioritized feature list

| Priority | V9-inspired feature | Usefulness to SNM+ | Safe integration path |
|---|---|---|---|
| **1 — highest (implemented in 3.64)** | **MX Lite / independent drawing controls**: V9 exposes signal visibility, iFVG visibility and recent-only presentation separately. | SNM+ already has a display-only `Clean` view and `Entry / stop / target lines = Last setup`, but older setup tags and iFVG boxes remain until the retained-setup cap removes them. `Show setups from grade` is an eligibility/display floor, **not** a drawing-only switch. | 3.64 adds an opt-in `MX Lite` view while leaving `Current (3.54)` as the default and preserving Clean. `Show setup labels` and `Show setup zones / iFVGs` independently hide only confirmed setup drawings; `Latest setup only (MX Lite)` defaults On but applies only to MX Lite. Older drawings are muted, not deleted, preserving retained setup records and tracker label IDs. `Setups kept on the chart`, grade floor, calculations, targets, alerts and outcome tracking are unchanged. ARMED/FORMING previews remain governed by their existing switch. Local AST/parser checks pass; TradingView compile/render/replay are still required. |
| **2 — high** | **Glanceable checklist with a distinct current-state row.** | V9's Bias/Status table and per-signal checks are easier to scan than a long hover card. SNM+ already has a Full panel, D/T/E rows, detailed setup tooltip and optional read-only Now row, so this is mainly clearer layout and state naming. | Reuse existing SNM+ values in a compact panel. Label the historical signal section `LAST SETUP`; label the live/confirmed evaluation row `NOW`. Use explicit states such as **pass**, **fail**, **not applicable**, and **not assessed**; disabled or unavailable checks must not look like failures. Keep D/T/E and the user's grade meanings. A V9-style confluence mark may describe presence, but must not become a veto, grade point, target change, or alert condition. Keep the current one-bar `PREV CLOSE` behavior and its confirmed-bar priority. |
| **3 — conditional** | **8AM / 9AM candle-range levels.** | These could add useful reference levels if they match the user's intended range model. SNM+ already has Premarket (08:00–09:30), the combined NY liquidity pool (09:30–16:00), and separate NY AM rulebook timing (09:30–11:00); none is automatically the same as V9's 8AM/9AM CR. | Before coding, specify each range's exact start/end, New York timezone/DST handling, when its high/low locks, how long it projects, reset/rollover behavior, and whether it is display-only or active liquidity. Safest first step: display-only levels with a default-off switch. Feeding them into SNM+'s active sweep/target registry would change model behavior and needs a separate, explicit behavior-specific request. Do not silently merge them into Premarket or NY. |
| **4 — later / explicit request** | **Standalone IFVG, LRL, HRL or SMT event alerts.** | V9 describes separate event-alert categories; SNM+ alerts are currently organized around its confirmed setup, ARMED/FORMING preview and rejected-trigger events. An event alert could be useful, but it adds a new alert surface and can be mistaken for a setup. | Only after defining the exact event for each alert (confirmed close versus wick, level touch versus break, SMT confirmation timing, deduplication and message fields), add separate opt-in categories. Respect the existing alert master, news blackout and trading/optional alert windows. Clearly name them as observations; do not create setups, change grades, or imply order execution. Forward TradingView alert logs are required to verify delivery. |

### Features already covered — prefer configuration, not duplication

- **Named liquidity and swept-level history:** SNM+ has Asia, London, Premarket, one combined 09:30–16:00 New York range, PDH/PDL and other named levels. Core session/PDH/PDL priority is additive to secondary levels; swept levels can remain visible from their chart anchor through the sweep bar. These are already the closest SNM+ equivalents to V9's session liquidity and `SSS` visuals.
- **HTF FVG context:** SNM+ has Fixed and optional chart-derived Auto timeframe slots, Grey / Tinted / Edges-only drawing styles, and a drawing switch separate from the gap calculations. Keep the existing `Fixed` default unless the user chooses Auto after replay comparison; screenshots from 3m to 4h are not a universal preset.
- **SMT and other checklist concepts:** SNM+ already has its NQ↔ES and MNQ↔MES Auto pairing, SMT/PSP, volume divergence, HTF delivery, V-shape, displacement, target/DOL, TTFM and existing rulebook checks. Presenting those more clearly is safer than adding another detector with the same label.
- **Recent setup plan lines:** `Entry / stop / target lines = Last setup` already removes older trade-plan lines while retaining older setup labels and iFVG boxes. MX Lite's latest-only mute complements that control by hiding older tags, trigger zones, trade-plan drawings and LRL markers without changing retained records or tracker outcomes.

For a no-code first trial on the current build, choose `Display → Chart view = Clean`, keep the checklist panel On at Auto, and optionally enable `Show setup state row (study)`. `Detail level = Full` retains richer setup-tooltip text, but Clean still uses the compact D/T/E panel. Keep `Entry / stop / target lines = Last setup`, `HTF gap boxes = Grey`, enabled session + PDH/PDL priority, and swept-level history as desired. This is a cleaner presentation, **not** a full MX-style checklist or a substitute for the separate MX Lite view. It does not alter setup qualification, grades, targets or alerts.

## Do not port as rules

- **V9 filter switches:** `All iFVGs In Leg Must Inverse`, HTF delivery, volume, Session DOL, LTF DOL, HRL, V-Shape and SMT options overlap with or differ from SNM+'s own checks. Do not turn them into new hard gates or alert vetoes. If useful, show only already-calculated SNM+ status in the checklist until the user explicitly specifies the behavior of a particular filter.
- **LRL / HRL definitions:** V9 narration describes a swing-joining LRL rail and a different HRL condition. SNM+'s LRL-touch count is a route-to-target measure; its operational HRL is a high/low made by a sweep. The ICT corpus uses its own low-/high-resistance liquidity concepts. Keep the definitions and labels distinct; do not copy a donor drawing or gate by name alone.
- **HTF mitigation:** because the screenshot and transcript conflict, retain SNM+'s current lifecycle and do not copy the V9 50%-wick or 100%-close rule without an explicit, behavior-specific decision.
- **V9 grade or performance claims:** do not import its grades, claim its reported double-sweep rate, or treat non-repainting/performance statements as verified by static screenshots.

## Staged integration and acceptance checks

### Stage 0 — configuration-first baseline (Clean / existing controls)

Try Clean and the settings above first. Keep `SMT sibling = Auto` for the supported NQ/ES and MNQ/MES pairs; on other instruments leave SMT off or select a confirmed valid manual feed. Keep the current Fixed HTF gap slots unless deliberately choosing Auto. These pair/timeframe choices are documented in `tools/snm-settings-by-pair.md`; no manual setting change should be required just because the chart timeframe changes.

### Stage 1 — implemented in 3.64; TradingView compilation verified

`Display → Chart view = MX Lite` now uses the existing Clean-style compact auxiliary drawings and, by default, mutes older confirmed setup drawings. The independent `Show setup labels` and `Show setup zones / iFVGs` switches default On; `Latest setup only (MX Lite)` defaults On but is ignored in Current and Clean. Current remains the default and retains the previous 3.63 drawing density; Clean remains available. None of these controls uses `Show setups from grade` as a hide switch, changes `iKeep`, deletes records/tracker IDs, or recalculates a different setup. Local AST/parser/lint checks pass, and the user confirmed the fixed build compiles in TradingView (CW10026/CW10003/CE10117 resolved). Toggle-on/off rendering, object retention and matched replay are still to be verified in TradingView before treating visual behavior as chart-verified.

### Stage 2 — implemented in 3.65

Built from the existing Full-panel and Now-row values, not new detectors. The panel now has a muted **LAST SETUP** header directly under the `SNM+ LONG/SHORT · grade` header, above the D/T/E rows (Simple) and the eight checklist rows (Full); the state row is labelled **NOW** in both panels. Checklist states are explicit: **✔** pass, **✖** fail, **n/a** when the check is disabled (TTFM closure with `TTFM → Off`; SMT/PSP with SMT off), and **–** when there is no data yet. A disabled or unavailable check no longer reads as a failure. D/T/E meanings, grades, the one-bar `PREV CLOSE` behaviour, confirmed-bar priority, setup qualification, targets and alerts are unchanged; no new input was added. The Now-row tooltip still states that `ELIGIBLE` is not alert delivery. Local AST/parser/lint checks pass; TradingView compile/render/replay remain to be verified.

### Stage 3 — only after definitions / request

Specify the candle-range lifecycle before adding 8AM/9AM levels. Specify individual event semantics before adding standalone alerts. Keep either feature independently switchable and default-preserving; an active-liquidity range or a new alert category must not be smuggled in as a display-only change.

### Regression and chart verification

For the implemented 3.64 view and any later display-only work:

1. The 3.64 AST regressions compare setup qualification, C/RB/RV classification, grades, target/stop selection, active liquidity/gap calculations, tracker/outcome logic and alert payloads against 3.63 while excluding only intended drawing changes. Positive controls detect changed grade/alert gates, destructive hiding and tracker writes that would reveal a hidden tag; retain this standard for later changes.
2. Test `Current`, `Clean`, `MX Lite`, and each independent visibility switch on the same symbol/feed, chart timeframe, date and replay endpoint. The confirmed setup bars, direction/model, grade, target/stop, level consumption, tracker result and alert eligibility must match; only visibility/layout should change.
3. Check object limits and refresh behavior when the latest-only option changes, when a new setup arrives, and when the optional outcome tracker updates an older setup. The display filter must not delete retained records or cause stale drawings to reappear incorrectly.
4. Run local Pine lint/parser/AST checks, then compile and inspect the rendered chart in TradingView. Local checks do not verify TradingView's compiler token budget, replay rendering, or alert delivery. Any new event alerts need forward-bar/alert-log checks separately.
5. Compare across the user's relevant pairs and timeframes without requiring manual retuning when switching chart TF. Keep pair-specific risk guidance and Auto/Fixed context documented in `tools/snm-settings-by-pair.md`.

**Decision:** Stage 1's display simplification was implemented in 3.64 and Stage 2's checklist clarity in 3.65; the views were removed in 3.68 and the extras in 3.69. New candle-range levels and standalone alert categories remain separate proposals. No SNM+ model semantics were changed by the display passes.
