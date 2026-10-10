// ⚠ NOT PINE CODE — this is a folder map for the Pine tooling in tools/.
// Paste the .pine files into TradingView; never paste a .md.

# tools/ — the Pine line

**The working script is `cisd-ultimate-balanced.pine`.** That is the file to paste into the Pine
editor. Everything else here is either documentation, verification tooling, or a set-aside revision.

## Layout

| path | what it is |
|---|---|
| `cisd-ultimate-balanced.pine` | the working indicator: CISD detector + iFVG registry + time engine (killzones, Silver Bullet hours, macro cores, NY AM opening range) + zone map. |
| `cisd-v1-guide.md` | how to use it: every switch and its default, the iFVG-at-the-open recipe, the panel legend, measured cost, and §7 - install and configure it on TradingView step by step, including how to confirm you are not looking at a stale build. |
| `cisd-audit.md` | the running record: what was found wrong in each revision, how it was verified, what the reference runtime cannot certify (§9d), and one section per round. Read §1-§2 for why the pasted v1's Noise Filter and sweep test could not do what their labels said. |
| `crt-candle-range-study.md` | the current phase: the 4H-candle-range / 01:30-sweep breakdowns you sent, inventoried element by element against the corpus, with the extend-vs-new verdict, the build spec (all switches named), and what I recommend not building. |
| `settings-by-pair.md` | the maintained settings matrix: what adapts to the timeframe on its own, what is derived, what you still set per pair and per session, plus the generated per-timeframe table and a starting configuration for FX / gold / indices. Update it in the same commit as any input change. |
| `tf-scale-table.py` | prints the markdown table that `settings-by-pair.md` and guide §6 quote, from the same formula the script ships. Re-run it rather than retyping numbers. |
| `mx-setups-study.md` | the setup inventory: what a reference set of iFVG/HTF-array screenshots actually contains, feature by feature, with the extend-vs-new build decision and the object/`request.security` budget that follows from it. This is the page the current phase (screenshots → new or refined tools) starts from. |
| `archive/` | set aside, not deleted: `cisd-ultimate-proper-v2.pine` (+ its guide) and `mx-context-overlay.pine` (+ its guide), the superseded `cisd-ultimate-journal.pine`, and `cisd-ultimate-balanced.pristine-v1.pine`, which is v1 exactly as it arrived so any decision in §13 of the audit can be reversed. |

## Verification, in this order

```bash
bash tools/pine-lint.sh tools/*.pine tools/archive/*.pine   # TV-parity type checker (primary)
python3 tools/pine-validate.py tools/*.pine tools/archive/*.pine
python3 tools/pine-validate.py --selftest                    # the checker's must-fire control
/home/user/venv/bin/pyne check tools/*.pine tools/archive/*.pine
python3 tools/pine-gate-run.py tools/*.pine                  # copy, execute, time, then the exercise variants
python3 tools/lint.py                                          # the markdown corpus, unrelated to Pine
```

The gate order now includes **calibrated exercises**: `pine-gate-run.py` re-runs each file's
`EXERCISES` variants with the default-off layers forced on, and a variant whose control counters stay at
zero fails the gate (`PROBLEM … ran but never fired`). That rule exists because a time-anchored layer on
pyne's 1-day synthetic bars compiles, runs, times clean and executes nothing — a green result from dead
code, twice in this directory.

`pine-lint.sh` clones and builds [pine-tools](https://github.com/folknor/pine-tools) on first use;
`pine-gate-run.py` needs `hoox-pyne` in `/home/user/venv` (rebuild recipe in audit §11). Both write
nothing into the repo. "Clean" means clean-as-compiled: editor-only argument gates and chart-legend
runtime errors are still possible, and no checker sees a table collision, an unbounded box, or a
checkpoint that awards itself a point — that class is what the audit sections are for.

## Conventions learned the hard way

* Every shipped `.pine` starts with `//@version=6` as literal line 1; every shipped `.md` in this
  folder starts with a `//` line saying it is NOT Pine code and naming the script it documents. A
  markdown file pasted into the editor produces a misleading "unspecified Pine version" error.
* TradingView caches the compiled build per script name: after an edit, delete the indicator
  instance and re-add it, and check the build tag in the legend before debugging anything else.
* Fix error *classes* across the whole file, not the line the editor pointed at.
* **Settings guidance is part of the build.** Any input added, renamed or re-defaulted in
  `cisd-ultimate-balanced.pine` comes with an update to `settings-by-pair.md` and to §1/§6 of
  `cisd-v1-guide.md`, and a re-run of `tf-scale-table.py` if it is a bar count. A per-pair matrix nobody
  maintains is worse than none, because it is believed.
* A number that cannot be traced to a measurement, a source, or arithmetic is not written down. Two
  figures were retracted this way (a 14x speed-up, and a "-0.216R after friction" citation that pointed at
  a study that was never run); `tools/cisd-audit.md` §14 and §15 record both.
* Prefer `input.timeframe` for timeframe inputs and pass it straight through; do not build a
  sanitizer for a restriction that only exists in the editor's argument gates.
