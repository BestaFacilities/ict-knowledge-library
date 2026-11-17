// NOT PINE CODE — workspace map for tools/snm-plus.pine (SNM+ 3.54, based on André Wonou's uploaded 3.47).

# Indicator workspace — SNM+ is the current project

The **working script is `tools/snm-plus.pine` (3.54)**; the exact uploaded 3.47 source is `tools/archive/snm-plus-3.47.pristine.txt` (SHA-256 `abbc9ffda5c39c2176b4695d4abc0096aa996d04a5d0e6787d94971815ea0b96`). Before the first integration pass, only `//@version=6` was moved to literal line 1; 3.48 added the first opt-in controls; 3.49 added the optional Auto gap ladder and stop-based drawing controls; 3.50 added default-off confirmed HTF CISD context; 3.51 added a conservative default-on hybrid HTF gap lifecycle and gaps containing price; 3.52 added default-off near-miss diagnostics for iFVG inversions; 3.53 trimmed the diagnostic to address TradingView CE10117 and separated the CISD minutes input to address CW10026; 3.54 adds visible codes and a latest-reason row so hover is unnecessary. Neither build has yet been confirmed against TradingView’s compiled-token limit. Do not mistake an archived predecessor for the active indicator.

## Here now

| Path | Purpose |
|---|---|
| `snm-plus.pine` | Active 3.54 indicator: 3.47 baseline plus default-preserving SMT symbol override, alert controls, same-sweep dedup, optional Auto gap ladder, stop-based Dim/Hide drawings, default-off confirmed HTF CISD context, hybrid HTF gap invalidation with breached-state drawings, and optional, lean iFVG near-miss codes + latest-reason row (no small-gap watchlist). |
| `snm-plus-guide.md`, `snm-settings-by-pair.md` | Current usage and maintained pair/timeframe settings; update with input changes. |
| `snm-integration-plan.md` | Feature-by-feature CISD Model+ comparison, shipped first pass and deferred experimental candidates. |
| `archive/legacy-indicators/` | Earlier CISD/CRT and ManipulationX scripts, studies, guides, settings matrix, and scale-table helper, moved here unchanged for retrieval. See its README. |
| `archive/` | Earlier archived indicator revisions, also retained unchanged. |
| `pine-lint.sh`, `pine-validate.py`, `pine-gate-run.py`, `tests/` | Pine compiler/validator/runtime smoke tests. These remain accessible at their original paths. Gate harness keys legacy exercises by filename, so pass the archived file path explicitly. |
| `lint.py`, `ingest_video.py` | ICT corpus maintenance, not SNM+ features. The `concepts/`, `raw/`, and other corpus directories are intact. |

The GitHub repository remains **active**. Only files in the current branch have been reorganized; its history and `master` have not been deleted, rewritten, or archived. Old guides' historical `tools/…` links still describe their original checkout paths; use the archive mapping instead. Do not edit frozen originals to disguise that change.

## Next work, now that the baseline file is present

1. Baseline captured: v6 compiler passed (22 warnings); pyne parser and raw 400-bar run succeeded. The AST validator's 12 false ARITY findings on omitted Pine-default parameters were removed by spelling out those defaults in the working copy. The pristine upload remains untouched.
2. Subsequent SNM+ passes: manual SMT symbol, alert categories/windows, same-sweep dedup, optional Auto gap ladder, stop-based Dim/Hide drawings, and confirmed HTF CISD context are in `snm-plus.pine`; Fixed/Keep/HTF-CISD-off still apply, but the 3.51 Hybrid gap lifecycle is a deliberate **default change**: confirmed HTF reclaim may allow later setups to differ from 3.50. Use Chart close plus gap-inside Off to reproduce 3.50; keep new Diagnostics Off to preserve 3.51 drawings. See `snm-plus-guide.md` and `snm-settings-by-pair.md` for usage and defaults.
3. The pyne object-mode runtime produces **no plot probes** for SNM+, so the `pine-gate-run.py` exercise correctly fails its must-fire requirement. Do not interpret the parser or raw run as a dynamic signal test. Next verify the toggle-on/off controls on TradingView/replay and pursue a runtime capable of exposing SNM+'s UDT/array state.
4. Consider the remaining opt-in features from `snm-integration-plan.md` only after comparison on charts; update the guide/matrix in the **same commit** as future input changes. No per-timeframe manual retuning required by default.

To test a legacy file after restoring the required external tooling, pass its explicit path, e.g. `python3 tools/pine-gate-run.py tools/archive/legacy-indicators/mx-replica.pine`. The gate script's paths in old comments/examples are historical, not instructions to use the archived script as the active project.
