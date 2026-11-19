// NOT PINE CODE — planning note for tools/snm-plus.pine (active source: SNM+ 3.63).

# Prioritized ManipulationX V9 → SNM+ roadmap

**Status: recommendations only.** Based on `tools/snm-manipulationx-v9-comparison.md`, the user's 11 screenshots (`image-38.png`–`image-48.png`) and video transcript, and the active SNM+ 3.63 source. No V9 code is being ported. This roadmap does not change SNM+ setup qualification, C/RB/RV model labels, D/T/E grading, targets, risk management, alerts, session rules, or timeframe behavior.

The screenshots show one saved V9 configuration, not verified factory defaults. In particular, the V9 screenshot and narration disagree about HTF FVG mitigation (50% / wicks versus 100% / close). Treat that donor rule as unresolved. The V9 performance and non-repainting claims are also unverified.

## Recommendation at a glance

1. **Start with SNM+ 3.63's existing Clean view** for a lighter chart; it is already display-only. No new feature is needed to try this.
2. If more of the V9 presentation is wanted, first add an **opt-in MX Lite display profile** with independent signal/zone visibility and a recent-setup-only drawing option. Keep the current view and Clean view intact.
3. Improve the compact checklist by reusing SNM+'s existing checks and clearly labelling **Last setup** separately from **Now**. This is information design, not a new qualification layer.
4. Treat the 8AM/9AM candle ranges and standalone event alerts as **later, separately specified proposals**. Their definitions or alert events are not complete enough to implement safely from the screenshots alone.
5. **Do not import V9 filters, grades, LRL/HRL constructions, mitigation rules, or performance claims as SNM+ behavior.**

## Prioritized feature list

| Priority | V9-inspired feature | Usefulness to SNM+ | Safe integration path |
|---|---|---|---|
| **1 — highest** | **MX Lite / independent drawing controls**: V9 exposes signal visibility, iFVG visibility and recent-only presentation separately. | SNM+ already has a display-only `Clean` view and `Entry / stop / target lines = Last setup`, but older setup tags and iFVG boxes remain until the retained-setup cap removes them. `Show setups from grade` is an eligibility/display floor, **not** a drawing-only switch. | Add an optional `MX Lite` view while leaving `Current (3.54)` and `Clean` unchanged. In that view, offer independent `Show setup tags`, `Show setup zones / iFVG labels`, and `Latest setup drawings only` controls. Keep the view opt-in; defaults outside it must reproduce 3.63. Hide/mute drawings rather than removing setup records or tracker references; do not change `Setups kept on the chart`, grade floor, setup calculations, alerts, or outcome tracking. Keep provisional ARMED/FORMING previews governed by their existing switch. |
| **2 — high** | **Glanceable checklist with a distinct current-state row.** | V9's Bias/Status table and per-signal checks are easier to scan than a long hover card. SNM+ already has a Full panel, D/T/E rows, detailed setup tooltip and optional read-only Now row, so this is mainly clearer layout and state naming. | Reuse existing SNM+ values in a compact panel. Label the historical signal section `LAST SETUP`; label the live/confirmed evaluation row `NOW`. Use explicit states such as **pass**, **fail**, **not applicable**, and **not assessed**; disabled or unavailable checks must not look like failures. Keep D/T/E and the user's grade meanings. A V9-style confluence mark may describe presence, but must not become a veto, grade point, target change, or alert condition. Keep the current one-bar `PREV CLOSE` behavior and its confirmed-bar priority. |
| **3 — conditional** | **8AM / 9AM candle-range levels.** | These could add useful reference levels if they match the user's intended range model. SNM+ already has Premarket (08:00–09:30), the combined NY liquidity pool (09:30–16:00), and separate NY AM rulebook timing (09:30–11:00); none is automatically the same as V9's 8AM/9AM CR. | Before coding, specify each range's exact start/end, New York timezone/DST handling, when its high/low locks, how long it projects, reset/rollover behavior, and whether it is display-only or active liquidity. Safest first step: display-only levels with a default-off switch. Feeding them into SNM+'s active sweep/target registry would change model behavior and needs a separate, explicit behavior-specific request. Do not silently merge them into Premarket or NY. |
| **4 — later / explicit request** | **Standalone IFVG, LRL, HRL or SMT event alerts.** | V9 describes separate event-alert categories; SNM+ alerts are currently organized around its confirmed setup, ARMED/FORMING preview and rejected-trigger events. An event alert could be useful, but it adds a new alert surface and can be mistaken for a setup. | Only after defining the exact event for each alert (confirmed close versus wick, level touch versus break, SMT confirmation timing, deduplication and message fields), add separate opt-in categories. Respect the existing alert master, news blackout and trading/optional alert windows. Clearly name them as observations; do not create setups, change grades, or imply order execution. Forward TradingView alert logs are required to verify delivery. |

### Features already covered — prefer configuration, not duplication

- **Named liquidity and swept-level history:** SNM+ has Asia, London, Premarket, one combined 09:30–16:00 New York range, PDH/PDL and other named levels. Core session/PDH/PDL priority is additive to secondary levels; swept levels can remain visible from their chart anchor through the sweep bar. These are already the closest SNM+ equivalents to V9's session liquidity and `SSS` visuals.
- **HTF FVG context:** SNM+ has Fixed and optional chart-derived Auto timeframe slots, Grey / Tinted / Edges-only drawing styles, and a drawing switch separate from the gap calculations. Keep the existing `Fixed` default unless the user chooses Auto after replay comparison; screenshots from 3m to 4h are not a universal preset.
- **SMT and other checklist concepts:** SNM+ already has its NQ↔ES and MNQ↔MES Auto pairing, SMT/PSP, volume divergence, HTF delivery, V-shape, displacement, target/DOL, TTFM and existing rulebook checks. Presenting those more clearly is safer than adding another detector with the same label.
- **Recent setup plan lines:** `Entry / stop / target lines = Last setup` already removes older trade-plan lines while retaining older setup labels and iFVG boxes. An MX Lite history option should complement this, not redefine it.

For a no-code first trial on the current build, choose `Display → Chart view = Clean`, keep the checklist panel On at Auto, and optionally enable `Show setup state row (study)`. `Detail level = Full` retains richer setup-tooltip text, but Clean still uses the compact D/T/E panel. Keep `Entry / stop / target lines = Last setup`, `HTF gap boxes = Grey`, enabled session + PDH/PDL priority, and swept-level history as desired. This is a cleaner presentation, **not** a full MX-style checklist and not an MX Lite implementation. It does not alter setup qualification, grades, targets or alerts.

## Do not port as rules

- **V9 filter switches:** `All iFVGs In Leg Must Inverse`, HTF delivery, volume, Session DOL, LTF DOL, HRL, V-Shape and SMT options overlap with or differ from SNM+'s own checks. Do not turn them into new hard gates or alert vetoes. If useful, show only already-calculated SNM+ status in the checklist until the user explicitly specifies the behavior of a particular filter.
- **LRL / HRL definitions:** V9 narration describes a swing-joining LRL rail and a different HRL condition. SNM+'s LRL-touch count is a route-to-target measure; its operational HRL is a high/low made by a sweep. The ICT corpus uses its own low-/high-resistance liquidity concepts. Keep the definitions and labels distinct; do not copy a donor drawing or gate by name alone.
- **HTF mitigation:** because the screenshot and transcript conflict, retain SNM+'s current lifecycle and do not copy the V9 50%-wick or 100%-close rule without an explicit, behavior-specific decision.
- **V9 grade or performance claims:** do not import its grades, claim its reported double-sweep rate, or treat non-repainting/performance statements as verified by static screenshots.

## Staged integration and acceptance checks

### Stage 0 — use the existing 3.63 controls

Try Clean and the settings above first. Keep `SMT sibling = Auto` for the supported NQ/ES and MNQ/MES pairs; on other instruments leave SMT off or select a confirmed valid manual feed. Keep the current Fixed HTF gap slots unless deliberately choosing Auto. These pair/timeframe choices are documented in `tools/snm-settings-by-pair.md`; no manual setting change should be required just because the chart timeframe changes.

### Stage 1 — optional display-only MX Lite

If the no-code profile is insufficient, implement the Priority 1 controls as a presentation layer only. The original Current view must remain the default and retain its 3.63 output; Clean must remain available. The new profile should not use `Show setups from grade` as a hide switch, change `iKeep`, or delete any object still referenced by the tracker. Turning the profile or individual display controls off must restore the relevant existing drawings without recalculating a different setup.

### Stage 2 — checklist clarity

Build from the current Full-panel and Now-row values, not new detectors. Every status must state what it refers to and whether the condition is applicable/assessed. A missing or disabled confluence check is not an automatic fail. The panel must distinguish the last completed setup from current/previous-close context and must not imply that `ELIGIBLE` guarantees TradingView alert delivery.

### Stage 3 — only after definitions / request

Specify the candle-range lifecycle before adding 8AM/9AM levels. Specify individual event semantics before adding standalone alerts. Keep either feature independently switchable and default-preserving; an active-liquidity range or a new alert category must not be smuggled in as a display-only change.

### Regression and chart verification

For any display-only implementation:

1. Add an AST regression comparing setup qualification, C/RB/RV classification, grades, target/stop selection, active liquidity/gap calculations, tracker/outcome logic and alert payloads against 3.63, while allowing only the intended drawing/panel nodes to differ. Include mutation controls proving the test catches a changed grade gate or alert path.
2. Test `Current`, `Clean`, `MX Lite`, and each independent visibility switch on the same symbol/feed, chart timeframe, date and replay endpoint. The confirmed setup bars, direction/model, grade, target/stop, level consumption, tracker result and alert eligibility must match; only visibility/layout should change.
3. Check object limits and refresh behavior when the latest-only option changes, when a new setup arrives, and when the optional outcome tracker updates an older setup. The display filter must not delete retained records or cause stale drawings to reappear incorrectly.
4. Run local Pine lint/parser/AST checks, then compile and inspect the rendered chart in TradingView. Local checks do not verify TradingView's compiler token budget, replay rendering, or alert delivery. Any new event alerts need forward-bar/alert-log checks separately.
5. Compare across the user's relevant pairs and timeframes without requiring manual retuning when switching chart TF. Keep pair-specific risk guidance and Auto/Fixed context documented in `tools/snm-settings-by-pair.md`.

**Decision:** recommend the staged display simplification first. The present request is for this prioritized plan; implementation of the optional view, new checklist, new range levels or new alert categories remains separate. No SNM+ model semantics have been changed by this roadmap.
