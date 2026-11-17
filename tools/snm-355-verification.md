// NOT PINE CODE — verification record for tools/snm-plus.pine (SNM+ 3.55); paste the .pine file, not this report, into TradingView.

# SNM+ 3.55 — verification record and TradingView handoff

**Source:** `tools/snm-plus.pine` at commit `78e49c1` on `arena/1ccc44fe-ict-knowledge-library`. **Reference:** 3.54 at `5b6c15a`. This is a verification checklist, not a claim that TradingView accepted 3.55 or that either view has equal market signals. No entry, grade or B-alert policy change is proposed here.

## Checks completed locally (2026-10-09)

| Check | Result | What it does not prove |
|---|---|---|
| Open-source Pine v6 checker, `bash tools/pine-lint.sh tools/snm-plus.pine` | 0 errors, 22 warnings (18 unused-variable, 4 conditional-series), same counts/classes as a local check of 3.54 | TradingView compiled-token/resource limits or its editor warnings. |
| AST derivative checker, `python3 tools/pine-validate.py tools/snm-plus.pine` | CLEAN, 0 findings | TradingView compilation or chart-time behavior. |
| AST checker positive control, `python3 tools/pine-validate.py --selftest` | PASS: fixture and real-control defects detected | A signal or alert from SNM+. |
| pyne parser, `/home/user/venv/bin/pyne check tools/snm-plus.pine` | OK | TradingView compiler parity. The ephemeral install was made with `python3 -m venv /home/user/venv` and `/home/user/venv/bin/pip install hoox-pyne numpy numba` in this turn. |
| Synthetic gate, `python3 tools/pine-gate-run.py --bars 240 tools/snm-plus.pine` | Script ran; **exit 1 / PROBLEM**: same-sweep confirmation probes never fired | Setup, Clean/Current equivalence, or runtime alert correctness. Do **not** mark this gate passed. |
| Corpus lint, `python3 tools/lint.py` | 287 concepts, 191 source IDs, 0 problems | Pine behavior. |
| Source review, `git diff 5b6c15a..78e49c1 -- tools/snm-plus.pine` | `cleanView` reads are confined to auxiliary drawing/panel paths; T-Spot history state updates remain outside the Clean drawing guard. The separate 3.55 changes adjust sizing text, tracker text and the Today A counter. | This is a static inspection, not a replay or a proof of equivalent alert execution. |

**Not yet checked:** TradingView compile of 3.55, its compiled-token count (3.52 previously hit CE10117), its warning list (3.52 also had CW10026), the Clean view's appearance and chart/runtime parity on a live feed. A 3.54 screenshot showed output on a chart but did not establish 3.55 compilation or an empty warning list.

## TradingView acceptance procedure — requires a user chart

1. Paste **the entire** `tools/snm-plus.pine` starting at literal line 1, `//@version=6`, into the Pine Editor, Save, Add to chart. Record the **compiler result, all warnings, and any resource/token message with line numbers**. The title should say **SNM+ 3.55**. Stop on any error; a local checker pass is not a substitute.
2. On **one identical chart/feed and NY trading date**, load 3.54 and 3.55 in separate chart layouts (or one at a time), copy all corresponding inputs exactly, and leave 3.55 `Display → Chart view = Current (3.54)`. Replay MNQ1! **1m** through a session with actual tags (including a B if available), then **3m**. Compare confirmed tag bar/side/model/grade, preview on the same candle, entry/stop/TP lines, and diagnostic reasons when enabled. Old vs new title, ticker/size wording, tracker status, and B-exclusion from Today A are **intentional** differences; drawings should otherwise keep 3.54 density. Do not compare unlike broker feeds or assume a later banner explains an earlier setup.
3. Within **3.55 only**, keep every other input fixed, switch `Chart view` between Current and Clean, and rerun the **same replay segment**. Confirm the same confirmed tags/grades, entry/stop/TP, Today count and diagnostic codes. Expected visual differences: at most one nearest level and HTF gap per side, at most one gap containing price if that display option is enabled, simple checklist even when Detail level is Full, and no timing ribbon, HTF candle/open, NWOG or T-Spot drawings. Turn `Draw T-Spots on the chart` on for a test segment with a closure to exercise its hide path; the T-Spot *check* should not change.
4. Repeat at least one segment on a **different instrument/feed actually used** (e.g. ES/MES or XAUUSD); check that chart ticker/point value/size text is meaningful. SIZE 0 is a warning to check risk budget and feed point value, **not** an order and **not** a signal veto. Do not manually retune settings for each timeframe simply to make the comparison pass; keep the same Fixed or Auto gap mode on both views.
5. Verify alerts separately **on forward/realtime bars when the platform supports them**: identical 3.55 alert settings under Current and Clean should yield the same alert category, time, side and payload. A historical replay tag alone cannot prove a server-side alert fired. The existing minimum-grade-B alert policy has **not** been changed; do not treat a B alert as permission to trade a hard-blocked setup.

**To report back:** symbol *with broker/feed*, chart timeframe, NY replay date/time or realtime timestamp, 3.54 vs 3.55 input differences (if any), 3.55 compiler errors/warnings (or explicitly none), two matched Current/Clean screenshots at the **same bar**, and any first differing tag/price or alert-log event. If there is no differing tag in the checked segment, report only that segment as matched—not global parity.

**Acceptance remains pending until steps 1–5 are observed.** Do not use this checklist or the synthetic gate as a performance/backtest claim.
