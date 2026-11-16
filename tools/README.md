// NOT PINE CODE — workspace map for SNM+ 3.47 (André Wonou), whose source was shared in chat but has not yet been added as a .pine file.

# Indicator workspace — SNM+ is the current project

The **current baseline is the user's SNM+ 3.47**, not the older CISD or ManipulationX experiments. Its complete source was pasted in the conversation; **there is no SNM+ `.pine` file in this checkout yet**. Do not mistake one of the archived scripts for the current indicator. Before modifying SNM+, save the exact uploaded source under `tools/archive/snm-plus-3.47.pristine.txt` and make a working copy at `tools/snm-plus.pine`. The pasted script places comments before `//@version=6`; move that directive to literal line 1 **only in the working `.pine` copy**, then compile it. Keep the pristine upload byte-identical so this normalization is auditable.

## Here now

| Path | Purpose |
|---|---|
| `snm-integration-plan.md` | Feature-by-feature comparison of SNM+ against the CISD Model+ reference sent by the user; safe candidates, known defects not to import, and verification plan. This is a plan, **not** an implemented merge. |
| `archive/legacy-indicators/` | Earlier CISD/CRT and ManipulationX scripts, studies, guides, settings matrix, and scale-table helper, moved here unchanged for retrieval. See its README. |
| `archive/` | Earlier archived indicator revisions, also retained unchanged. |
| `pine-lint.sh`, `pine-validate.py`, `pine-gate-run.py`, `tests/` | Pine compiler/validator/runtime smoke tests. These remain accessible at their original paths. Gate harness keys legacy exercises by filename, so pass the archived file path explicitly. |
| `lint.py`, `ingest_video.py` | ICT corpus maintenance, not SNM+ features. The `concepts/`, `raw/`, and other corpus directories are intact. |

The GitHub repository remains **active**. Only files in the current branch have been reorganized; its history and `master` have not been deleted, rewritten, or archived. Old guides' historical `tools/…` links still describe their original checkout paths; use the archive mapping instead. Do not edit frozen originals to disguise that change.

## Next work, when the baseline file arrives

1. Capture the pasted SNM+ 3.47 source byte-for-byte as a pristine `.txt`, normalize only the working `.pine` copy's version directive to literal line 1, and verify that copy with the real Pine compiler, AST validator (including its must-fire control), and runtime gate where supported. Record limitations explicitly; do not claim the pasted code was compiled before it was made available as a file.
2. Apply the approved portable features from `snm-integration-plan.md` as **optional switches** in SNM+ rather than transplanting the other indicator wholesale. Preserve SNM+'s DTE grade scale, model names, colours, object budget, and default signal semantics unless a correction is demonstrated.
3. Create/update a SNM+ usage guide and pair/timeframe settings matrix in the **same commit** as input or default changes. No per-timeframe manual retuning required by default.
4. Re-run the gates with positive-fire controls for the new branches; inspect side-by-side TradingView charts for non-repainting and chart readability.

To test a legacy file after restoring the required external tooling, pass its explicit path, e.g. `python3 tools/pine-gate-run.py tools/archive/legacy-indicators/mx-replica.pine`. The gate script's paths in old comments/examples are historical, not instructions to use the archived script as the active project.
