// ⚠ NOT PINE CODE — this is a folder map for the Pine tooling in tools/.
// Paste the .pine files into TradingView; never paste a .md.

# tools/ — the Pine line

**The working script is `cisd-ultimate-balanced.pine`.** That is the file to paste into the Pine
editor. Everything else here is either documentation, verification tooling, or a set-aside revision.

## Layout

| path | what it is |
|---|---|
| `cisd-ultimate-balanced.pine` | the working indicator: CISD detector + iFVG registry + time engine (killzones, Silver Bullet hours, macro cores, NY AM opening range) + zone map. |
| `cisd-v1-guide.md` | how to use it: every switch and its default, the iFVG-at-the-open recipe, the panel legend, measured cost. |
| `cisd-audit.md` | the running record: what was found wrong in each revision, how it was verified, what the reference runtime cannot certify (§9d), and one section per round. Read §1-§2 for why the pasted v1's Noise Filter and sweep test could not do what their labels said. |
| `crt-candle-range-study.md` | the current phase: the 4H-candle-range / 01:30-sweep breakdowns you sent, inventoried element by element against the corpus, with the extend-vs-new verdict, the build spec (all switches named), and what I recommend not building. |
| `mx-setups-study.md` | the setup inventory: what a reference set of iFVG/HTF-array screenshots actually contains, feature by feature, with the extend-vs-new build decision and the object/`request.security` budget that follows from it. This is the page the current phase (screenshots → new or refined tools) starts from. |
| `archive/` | set aside, not deleted: `cisd-ultimate-proper-v2.pine` (+ its guide) and `mx-context-overlay.pine` (+ its guide), the superseded `cisd-ultimate-journal.pine`, and `cisd-ultimate-balanced.pristine-v1.pine`, which is v1 exactly as it arrived so any decision in §13 of the audit can be reversed. |

## Verification, in this order

```bash
bash tools/pine-lint.sh tools/*.pine tools/archive/*.pine   # TV-parity type checker (primary)
python3 tools/pine-validate.py tools/*.pine tools/archive/*.pine
python3 tools/pine-validate.py --selftest                    # the checker's must-fire control
/home/user/venv/bin/pyne check tools/*.pine tools/archive/*.pine
python3 tools/pine-gate-run.py tools/*.pine                  # build a runnable copy, execute, time
python3 tools/lint.py                                          # the markdown corpus, unrelated to Pine
```

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
* Prefer `input.timeframe` for timeframe inputs and pass it straight through; do not build a
  sanitizer for a restriction that only exists in the editor's argument gates.
