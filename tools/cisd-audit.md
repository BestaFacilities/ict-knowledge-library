// ⚠ NOT PINE CODE — this is the audit write-up. The script is tools/archive/cisd-ultimate-proper-v2.pine

# CISD Ultimate Balanced — audit & rebuild notes

**Date:** 2026-10-09 to 2026-10-10 (§13 is the current revision) · **Subject:** `tools/cisd-ultimate-balanced.pine` (the pasted v1) → `tools/archive/cisd-ultimate-proper-v2.pine`
**Method:** every claim below is checked against a concept page in this library, and the two
quantified findings were measured by porting the v1 code to Python and running it on synthetic
OHLC (random walk, 20 000 and 8 000 bars, symmetric candle direction).

---

## 1. The measurement that matters most

### 1a. The Noise Filter cannot reject anything, and it biases the indicator short

v1's CISD core scores a ratio and gates it on `tolerence` (0.55–0.66):

```pine
float ratio = (highest - array.first(bear_potential)) / math.max(top - array.first(bear_potential), syminfo.mintick)
if ratio > tolerence      // ← gate
```

Two structural problems:

* `highest` is the max close over the whole run, `top` is an open **inside** that run, so
  `highest ≥ top` and the ratio is `≥ 1` by construction. A threshold below 1 can only ever
  pass. Measured: **87.6 % of evaluations passed**, median ratio **2.78**, i.e. the input is
  decoration.
* `top` / `bottom` are initialised to `0.0` and only written inside the `while running` walk.
  If the first candle after the pivot is not in the expected colour, the walk exits immediately
  and the denominator degenerates:
  * bear side → `math.max(0.0 − price, mintick)` = **one tick** → ratio explodes → **auto-pass**
  * bull side → `math.max(price − 0.0, mintick)` = **the price level** → ratio ≈ 0 → **auto-fail**

  That path is hit **54 %** of the time. Measured outcome on a walk with no directional bias:
  **2 219 bear signals vs 47 bull signals — a 47× asymmetry**, and a bear "state change" on
  **11 % of all bars**.

So the pattern v1 actually detects is: *a candle closes opposite to its neighbour, and later
price closes back through that candle's open*. That is a two-candle engulf + reclaim. It is
momentum, not a change in the state of delivery, and its filter is one-sided.

### 1b. A "sweep" that closes through the level is a break, not a sweep

`concepts/02-liquidity/liquidity-sweep.md` gives the arithmetic:

```
BSL_sweep := high_n > level AND close_n < level AND (high_n − close_n) > 0.6 × range_n
```

v1 uses `if high >= lvl` and sets `wicked_high := true`. Measured on 8 000 bars of synthetic
data with pivot levels: of everything v1 counted as a sweep, **89 % closed through the level**
(a structural break by the corpus's own sentence *"a sweep wicks; BOS closes"*), and only **1 %**
met the full definition. The sweep confluence — the step the whole 2022 model hangs on — is
diluted ~100×.

---

## 2. Findings, one by one

| # | v1 | corpus | fix in v2 |
|---|---|---|---|
| 1 | CISD = close beyond a **candle open** | `order-flow-shift.md`, `mss.md`: a **close through a confirmed swing**, with displacement, leaving an FVG | shift = close through a live pivot; displacement-scored; requires an array left behind |
| 2 | ratio gate (see 1a) | `displacement-strength-criteria.md`: 5 factors → 5–15, 12+ strong | `f_dispAt()` implements the rubric; gates on score, not on a broken ratio |
| 3 | touch = sweep (see 1b) | `liquidity-sweep.md` | wick through **and** close back **and** wick ≥ `wickMin` × range; close through = state "broken", a different event |
| 4 | levels = pivots only | pools are Asian range, PDH/PDL, session highs/lows **and** swings | raids checked against all of them; `raidPx` carried into the stop |
| 5 | all model steps are optional toggles, off by default; gate = `score ≥ 2` of 5 | `ict-2022-model.md`: bias ∧ KZ ∧ sweep ∧ displacement-with-FVG ∧ entry at the array ∧ SL beyond the sweep | chain inputs default **on**; score now *grades* what passes (A+/A/B/C) instead of replacing the chain |
| 6 | signal block has no `barstate.isconfirmed` | — | gated; v1 could print an alert mid-bar on a candle that then closed differently |
| 7 | `request.security(..., close)` / `ta.ema(...)` on HTF, no `lookahead` | — | reads `[1]` with `lookahead_on` = the last **completed** HTF bar. v1's version is look-ahead biased in history, which silently inflates any backtest of the HTF confluence |
| 8 | FVG = any 3-candle gap over 0.40 ATR | `fair-value-gap.md` criterion c3: candle n **must** be displacement | `fvgNeedDisp` + `fvgDispMin` on the middle candle's 4-factor core score |
| 9 | FVG removed when price crosses the far edge | `ce-as-primary-entry.md`, `fvg-mitigation.md` | states: fresh → CE worked → filled → **inverted** (close through the far edge), with per-zone state |
| 10 | one global `last_bull_fvg_*` slot | — | full store; the shift picks the **nearest qualifying** array instead of "whatever formed last" |
| 11 | iFVG = `close > last_bear_fvg_top` within 12 bars | `inversion-fvg.md` | inversion = close through the far edge, recorded as a state on the zone, and it then serves the flipped direction on retest |
| 12 | OB = any down-candle before an up-candle, zone = `high[1]/low[1]` | `order-block-criteria.md`: last opposite candle **before displacement**, displacement **breaks structure**, run of same-colour candles = **one** block, bodies by default, tiny/encapsulated bodies rejected, spent after mitigation | `f_frame()` walks the run, `obZoneMode`, size rejection, touch counter with `obTouchMax`, spent blocks deleted |
| 13 | premium/discount vs `ta.highest(high,25)` | `dealing-range.md`: **unbroken LTH/LTL**, re-anchored on an external break | dealing range from live (unbroken) levels; EQ, OTE 0.62 band as a modifier |
| 14 | Asia "killzone" 18:00–22:00 | `killzone-times-table.md`: Asia **20:00–00:00**; London 02–05; NY AM 08–11; **London close 10–12**; **NY PM 13:30–16** | all five, plus a 2017-set switch (the file's warning: *"state which set is in use"*), and macro / silver-bullet sub-windows |
| 15 | entry = market at close, SL = 0.35 ATR past the bar | steps 5–6: entry on the array at CE, SL beyond the **swept** extreme | `entryDepth` (near/CE/far), `slMode` (sweep / array / ATR) |
| 16 | TP = fixed RR, liquidity target drawn but unused | step 7: targets via the draw on liquidity | `f_poolAbove/f_poolBelow` = **nearest** pool; `tpMode` pool / fixed / both |
| 17 | mitigated swing lines removed from the array but **not deleted** when `hide_mitigated_levels=false` | — | every state change deletes or restyles the object; no orphans |
| 18 | `live_fvg_labels` shared by the bull and bear arrays, deleted by index of the other | — | one object per record, popped with its record |
| 19 | `if array.size(x) > 0 / for i = size-1 to 0 / if i < array.size(x)` | — | direct descending loops (the inner guard was dead code) |
| 20 | `"Cooldownoldown"` | — | fixed |

## 3. v2 architecture

```
pivots → level store (live / swept / broken / expired)
      → dealing range → EQ, premium/discount, OTE
      → raid detection (swings + PDH/PDL + Asia + London)  → raidBar, raidSide, raidPx
      → close through a live level = SHIFT candidate (bar t)
      → t+2: score the break candle with follow-through, check the chain,
             pick the nearest array the leg left behind, place entry/SL/TP
      → ARMED (limit, not a market call)
      → price trades into the array → FILLED
      → TP / SL / time-stop → journal record; or VOID if the sweep takes out the stop
             before the array is ever reached
```

Two-stage by design: `order-flow-shift.md` says confirmation comes from the follow-up bars, and
factor 5 of the displacement rubric does not exist at the moment the break prints. Judging the
break at `t+2` is what makes the score mean something.

The visual vocabulary changed with it: v1 stamped a `BEST` label at the close of the signal bar.
v2 draws `ARM → FILL → TP/SL/VOID`, because an armed setup that never traded into the array is a
different event from one that filled and failed, and conflating them makes the statistics
uninterpretable. `ARM→FILL` in the dashboard is itself a number worth watching: if very few armed
setups ever fill, the entry depth is too passive and `entryDepth` should move toward the near edge.

## 4. Honest limits of v2

* **No intrabar sequence.** A bar that spans CE and the stop is still a guess; the tie-break input
  and the `AMBIG` count exist so the guess is visible, not hidden.
* **Follow-through costs two bars.** v2 arms late by construction. That is the price of a signal
  that does not repaint; it is not a delay you can take in real time, so the alert is *arm*, and
  the fill is yours to decide.
* **Displacement scoring is calibrated on single candles.** The corpus describes the rubric
  qualitatively; the 0.85 / 0.70 / 0.50 body bands and the ×1.0/1.5/2.0 body-vs-average steps are
  the page's numbers, but the mapping from "wide FVG inside" to a 3/2/1 was a judgement call.
* **The journal is still a journal, not a broker.** Fixed contract size, no commissions beyond
  `cost` in R units, no partial fills, no swap.
* Nothing here has been through TradingView's own compiler — that only runs in their editor.
  What has been done instead is documented in §5: a real Pine v6 grammar + interpreter plus the
  v6 builtin table, with the checks calibrated against the user's own v1 file. The R/statistics
  arithmetic was additionally cross-checked against a brute-force recomputation in Python.

## 5. Compile-readiness (round 2): what the editor found, and how it was checked after

Two rounds of real TradingView diagnostics were fed back into this script. Both classes were
fixed across the whole file, not just at the quoted line.

| Report | Root cause | Fix |
|---|---|---|
| `CE10150 "to" cannot be used as a variable` | `to` is a keyword (`for i = 0 **to** n`) | renamed the time-stop flag to `timedOut` |
| `CW10003 should be called on each calculation` on `ta.highest/lowest(…, 240)` | `ta.*` inside `if drHi == 0.0` | hoisted to global `hhFallback` / `llFallback`; the `if` only picks |
| `CW10003` on `[pCore, pTot] = f_dispAt(2, pDir)` | user fn reads series with a **variable** offset → its locals become self-referencing state | score both directions every bar (`brkTotUp` / `brkTotDn`), pick with a ternary |
| `CE10272 Undeclared identifier "jn"` | **block scoping**: declared inside `if showDash …`, used inside the sibling `if btOn and btShow …` | use the journal block's own locals (`has`, `w_t`, `l_n`) |
| 3 × `f_frame(...)` inside `if` (found by the checker, not yet reported by the editor) | same rule as `f_dispAt` | `f_frame(±1, 1)` and `f_frame(±1, 3)` hoisted to global, picked by `pDir` |

**Language rules that actually bind here** (learned from a v6 grammar/reference, not from memory):

1. *Local scopes do not intersect.* A name declared in an `if` body exists only in that body and
   its children — never in a sibling block, and never back at global scope. This is the single
   most common failure in a script written as one flat narrative with two panels.
2. *"Should be called on each calculation"* is not limited to `ta.*`: any user function whose body
   touches `ta.*`, `request.*`, `var`, or indexes a series with a non-constant offset
   (`close[k]`, `avgBody[k]`) inherits it. Calling it on a conditional path desynchronises the
   series — a wrong number, not just a lint.
3. v6 lazily evaluates `and` / `or`, so a stateful call in the right operand is *skipped*, not
   merely warned about.
4. v6 integer division returns float (`5 / 2 = 2.5`): an `int` context containing `/` is a type
   error unless wrapped in `int()`.
5. `na()` / `nz()` reject `bool` in v6; bools can no longer be `na`.
6. Tuple destructuring arity must match the returned tuple exactly; `_` discards an element
   (`[obH, obL, _] = f_frame(1, 3)`).
7. Hard caps worth knowing for a script this size: 40 `request.*` calls, 64 plots, 500
   lines/boxes/labels, ~100 000 compiled tokens, 1 000 variables per scope. This script uses 5
   security calls, 8 plots, and ≈7.7k lexical tokens, so there is headroom.
8. *A function may not assign to a global.* It can read one and it can call methods on one
   (`array.remove(kzY, i)`, `line.set_x2(l, bar_index)`), but `counter += 1` on a global scalar inside a
   function body is `Cannot modify global variable "counter" in function`. Mutators for global counters
   belong at the call sites, guarded the same way the function guards them. Learned writing the `grp_kzl`
   layer (§17); `pyne check` said nothing about it.

**How it was verified in the sandbox.** `hoox-pyne` (ANTLR v6 grammar + AST + object-mode
interpreter) gives `pyne check` / `pyne lint` / `pyne run`, and ships the TradingView v6 builtin
table; on top of it three checks were written and *calibrated against the untouched v1 file*
(every hit that v1 also produced was treated as a false positive and the rule was tightened until
only the classes TradingView itself reports remain):

* scope resolution over the real AST — 3 073 name loads, 142 `if` blocks, 16 loops: 0 unresolved;
* tuple-arity check across all 12 user functions and every `request.security` call site: clean;
* v6 type-direction check (int-vs-float flow, `str.tostring` formats): clean;
* all 52 namespaced builtin calls resolve against the v6 table — no invented functions;
* `pyne run` executes the full script on synthetic bars without error.

`pyne lint` still reports 80 `C002` warnings: lines longer than 120 characters. That is this
linter's style default, not a Pine rule — the Pine editor has no line-length limit. Say the word
and the dashboard and journal rows get wrapped, but they are the noisiest part of the diff.

**Corrected 2026-10-10 (was: "not fixed on purpose"):** the four `CW10003` sites in
`cisd-ultimate-balanced.pine` (the pasted v1) and `cisd-ultimate-journal.pine` - `ta.highest` /
`ta.lowest` in a conditional, `get_liq_target()` called conditionally - were later hoisted to global
scope in both files (`recent_high`/`recent_low` at column 0; `liqHi18`/`liqLo18` computed once with
the reason in a comment above them; `get_liq_target()` now reads hoisted globals, so calling it from
inside a branch is legal). Nothing in v1 is left unfixed on purpose. What v1 still does NOT have is
any of v2's model work - the ratio gate repair, the sweep definition, the funnel - because v1 is the
as-received baseline, and since the 2026-10-10 decision it is also the working file again: v2 and the
overlay are set aside, not deleted, so anything in them can still be lifted across deliberately.

## 6. Runtime round (round 3): the empty-array `for` crash, in full

TradingView then reported, not a compile error but a runtime one:

    Error on bar 5414: In 'array.get()' function. Index 0 is out of bounds, array size is 0.

**Cause.** A counted `for` in Pine executes its body *before* it first tests the end boundary. So
when the journal is empty, `for i = 0 to array.size(jr) - 1` becomes `for i = 0 to -1` — and the
body still runs once, with `i = 0`, against an array of size 0. Verified in the sandbox with a
three-bar control script: the empty-array loop accumulated iterations (it ran 2× per 3 bars, vs
3× for a 3-element array), i.e. the body is not skipped when `end < start`.

**Where.** All ten `for` loops in v2 were audited by hand. Nine were already guarded by an
enclosing `if array.size(x) > 0` (or `m > 0`); the journal aggregation loop was not, because its
bound is a local `int m`, and the only `m > 0` test sitting above it guards a *sibling* loop
(the `btLook` start-index scan), not this one.

**Fix** — `i >= m` rather than `m > 0`, because the same class also fires on the *overshoot*
case: when every recorded trade is older than `btLook`, `firstIdx` ends up equal to `m`, and
`for i = m to m - 1` would run once with `i == m`:

```pine
for i = firstIdx to m - 1
    if i >= m
        continue
    float v = array.get(jr, i)
```

**Adjacent risks checked at the same time, all clean:** the four parallel-array groups
(`lv*`, `g*`, `o*`, `j*`) are appended and trimmed in exact lockstep, so an index valid for one
member is valid for all; `J`/`K` are fixed 20/12 slots and the highest index touched is 17/10;
every `line.delete` / `box.delete` / `label.delete` is behind a `not na()` test; every division
by a count is inside a `> 0` ternary. `array.pop`/`array.shift` calls all sit under
`while array.size(x) > N`.

**The first fix was wrong, and the second report explains why.** The guard was `if i >= m`, which
assumes the loop runs once. It runs *twice*: `for i = a to b` derives its **direction** from `a` vs
`b` and includes `b`, so `for i = 0 to -1` iterates `i = 0`, then `i = -1`. The upper clamp killed
the first read and walked straight into the second — `Index -1 is out of bounds, array size is 0`.
A one-sided guard is therefore never enough for this class; the bound must be clamped both ways:

```pine
for i = firstIdx to m - 1
    if i < firstIdx or i >= m      // lower AND upper
        continue
    float v = array.get(jr, i)
```

The lower half is not decorative: when every recorded trade is older than `btLook`, `firstIdx`
ends up equal to `m`, the loop counts *down* `m, m - 1`, and `i == m - 1` is a perfectly valid
index — so the loop would report exactly one trade, silently, instead of none. Clamping to
`[firstIdx, m)` fixes both the crash and that wrong-number case.

**Systemic fix, not a spot fix.** A counted loop that indexes an array by its own loop variable is
unsafe *by syntax*, whatever the enclosing `if` says — the guard above it is a separate scope and a
future edit can drop it. So all ten `for` loops in v2 were rewritten to carry the clamp as their
first body statement (9 got `if i < 0 or i >= array.size(X)`, the journal loop got the
`firstIdx`-relative form above). The enclosing `if array.size(x) > 0` blocks were kept: they still
avoid the pointless call, but nothing depends on them for correctness.

The rule now enforced mechanically by `pineaudit.py` (`LOOP-CLAMP`): *every* `for` whose body
indexes an array by the loop variable must have a lower bound, an upper bound and a `continue` as
its opening statement. No proof, no dependence on surrounding conditions. It flags 10 sites on the
pre-fix file, and the half-guard version above is exactly the state it was written to reject.

**Everything else in the runtime-error family, checked and clean:**

| Risk | Result |
|---|---|
| `table.cell` column/row outside the `table.new` grid (`dash` 4×9, `jt` 6×13; `f_jcell` writes `col` and `col+1`) | in range, max 5/8 |
| Literal index into a fixed array (`J` = 20 slots, `K` = 12) | max used 17 / 10 |
| Parallel arrays (`lv*`, `g*`, `o*`, `j*` — 13 journal arrays since §7c) drifting out of lockstep | appended and trimmed in exact lockstep at every site, so a clamp on the bound array covers the other reads |
| `line.delete` / `box.delete` / `label.delete` on `na` | all behind `not na()` |
| Division by a count (`n`, `n_t`, `w_t`, `l_n`) | all inside `> 0` ternaries; the R-normalising divisor uses `math.max(…, syminfo.mintick)` |
| `array.pop` / `array.shift` on an empty array | every call sits under `while array.size(x) > N` |

**Still unverifiable offline, and what it would look like:** the dynamic history offsets in
`f_dispAt` (`high[k]`) and `f_frame` (`close[from]`, `high[k]`) are legal v6, but if TradingView's
automatic lookback detection refuses to size them it reports *"Cannot determine referencing
length"*. The fix is one line per series — `max_bars_back(avgBody, 20)` — and it is worth adding
only if that exact message appears, because `max_bars_back` pins memory for every symbol.

Idioms to keep in mind when writing this again: prefer `for [i, v] in arr` (zero iterations when
empty, no bound arithmetic at all), or `while i < n` — both are empty-safe by construction, unlike
`for i = 0 to n - 1`. And in Pine, never treat `for i = a to b` as "runs only if a ≤ b": it always
runs at least once.

---

## 7. v2.1 — timeframe scaling, dead inputs, journal depth

Prompt: *"full guide on the best ways to use this indicator, the best full settings according to
the TF I am on (if I can set presets for the different TFs, would be better)"*. Guide written to
`tools/archive/cisd-v2-guide.md`; this section records what changed in the code and how it was checked.

### 7a. The preset ladder existed but was manual and bar-denominated

v2 already had a `Preset` `input.string` with an `if preset == …` block overriding seven parameters
— but the user had to pick the row by hand, and every *duration* in the script (`Level expiry`,
`array stays valid`, `armed this many bars`, `sweep within`, `cooldown`) was an absolute bar count.
So on a 1H chart "18 bars armed" is 18 hours, and on 1m it is 18 minutes: same setting, different
model. That is the gap the request was really pointing at.

Fix: `Preset` gained an `Auto (chart TF)` option (now the default) that maps
`timeframe.in_seconds()` onto the same row index (0 = 1min … 10 = daily), and the five duration
inputs became minute-denominated, converted by one pure helper:

```pine
f_bars(float minutes, int minBars) =>
    math.max(minBars, math.min(20000, math.round(minutes * 60.0 / tfSec)))
```

Windows therefore carry their meaning across timeframes, and the floors only bite where the minute
value stops being meaningful (a window can never be shorter than the number of candles the test
itself needs: expiry 12, array 4, arm 2, sweep 3, cooldown 0). First cut used floors of 60/8/3/6,
which silently overrode the conversion at 1H and above and turned a 10-hour expiry into 2.5 days —
caught by printing the resolved table for every TF before shipping it, not by the compiler.
`TF / WILSON` in the journal prints the row chosen and the resolved bars, so the chart states what
it is doing instead of the documentation promising it.

Structural knobs became `0 = from preset` overrides (`swLenIn`, `dispMinIn`, `dispAIn`,
`fvgMinAtrIn`): the ladder wins when the input is 0, the user wins when it is not. `dispLook` is
deliberately *not* scaled — it feeds `ta.sma(…, dispLook)`, whose length argument must be a
`simple int` (v6 reference), so a value derived from `timeframe.in_seconds()` would not compile;
and factor 3 of the displacement rubric compares a body against the *average nearby body*, which is
a relative measure and so already timeframe-free. Candles are the correct unit for it.

### 7b. Three dead inputs, found by counting uses of every `input.*` identifier

| Input | Symptom | Resolution |
|---|---|---|
| `Levels tracked per side` (`swMaxKeep`) | declared, never read; `maxKeep` was hard-coded `40` | wired: `int maxKeep = math.max(4, swMaxKeep)` |
| `Frame a same-colour run as ONE block` (`obRunFrame`) | declared, never read; `f_frame` always framed runs | wired: `int obRun = obRunFrame ? obMaxRun : 1`, used in the run-extension `while` |
| `Session/day pool stays live (bars)` (`poolExpiry`) | declared, never read; no mechanism existed | **removed** rather than faked — pools expire by session construction (PDH/PDL per day, Asian/London ranges reset on their own session flags) |

The check is one loop over `^(\w+) = input\.` and a use-count of the identifier — a declared input
the script never reads is worse than no input, because it lets the user believe a knob is connected
to something. An earlier round shipped exactly that: the label promised behaviour the code did not
have. Run this check on every revision; it costs seconds.

### 7c. Journal depth, so "best settings" is a measurement and not an opinion

Per-trade records gained `jzone` (killzone bucket at the arm: Asia / London / NY AM / LC+PM /
off-clock), `jkind` (FVG / iFVG / OB / level-only) and `jent` (entry price, for the markers).
The table grew from 6×9 to 6×13 with per-bucket expectancy cells and an R-multiple histogram plus
`TAIL ≤-2R` / `CLIP ≥2R` counters. New arrays are pushed and shifted in exact lockstep with the
existing twelve, re-checked by counting `array.push`/`array.shift` per name (13/13).

`VERDICT` no longer reads the sample mean. It compares the **Wilson 95% lower bound** of the win
rate against the break-even rate implied by the average R — because at n = 12, 8W/4L is not 67%,
it is "somewhere above 34%", and 34% does not clear break-even at 2R. `f_wilsonLo` is closed-form
z = 1.96 arithmetic, no iteration, no `ta.*`.

### 7d. `alert()` payload and last-bar markers

`alertOn` + `alertFmt` emit `ARM / FILL / TP / SL / VOID` through `alert()` with a JSON (or plain
text) payload — event, symbol, tf, dir, grade, score, array kind, entry/sl/tp at `format.mintick`,
target R, bars since the arm — fired on `barstate.isconfirmed` only, beside the existing static
`alertcondition`s rather than replacing them. `showMarks`/`markN` draw ±R labels at each journalled
entry price, rebuilt inside the last bar from a `label[]` array that is popped and deleted first, so
object use stays flat at `markN` regardless of chart length.

One avoidable compile error was sidestepped here: `na()` on a `label`/`line`/`box` variable is
`na`-on-bool, since those primitive types are bool-backed in the v6 type system (same trap as the
unused tuple slot `_ = bool` in `f_jcell`, §5). The marker cleanup therefore deletes
`array.pop(mLbl)` directly — every element is a real `label.new()` result, so no guard is needed.

### 7e. Checks run on this revision

`pyne check` OK · `pyne run --bars 250/500/600/800/1500` OK · `pinescope` (18 functions, stateful:
`f_dispAt`, `f_frame`) CLEAN · `pinetuple` CLEAN · `pinetype` CLEAN (301 typed globals) ·
`pineaudit` CLEAN (LOOP-CLAMP / TABLE-CELL / ARR-LEN, calibrated against `/tmp/state_a_none.pine`
and `/tmp/state_b_half.pine`, both of which still fire).

The LOOP-CLAMP rule was refined this round: it now fires only where the loop bound is *size-derived*
(`array.size(...)` or a size variable), because `for k = 0 to 5` over a fixed six-slot array — used
by `f_hist` — cannot be empty and needs no clamp. A rule that flags safe code gets disabled by
people, which is worse than no rule.

The same clamp sweep was applied to `cisd-ultimate-journal.pine` (15 loops) and
`cisd-ultimate-balanced.pine` (12 loops) so that whichever file gets pasted is bounds-safe; both
re-validated clean (`check` OK, `run --bars 500` OK, `pineaudit` 0 findings, scope/tuple/type CLEAN).
v2 remains the only supported entry point; those two are kept for the diff history.

CLI note for the next session: `pyne run` accepts only `--encoding`, `--bars`, `--json`, `-q`. The
symbol/interval/no-output flags do not exist — the runner uses a deterministic synthetic series.

---

## 8. v2.2 — the clutter pass

The chart the user pasted (XAUUSD 5m) was legible nowhere: ~48 horizontal level lines each drawn
with `extend = extend.right`, one FVG/OB band per gap ever made (also `extend.right`), a full-width
delivery plot, and 110 table cells of which a third were translucent text on a dark background.
None of it was a bug — all of it was *accumulation*, which is what an indicator that models state
does when it renders state without ranking it.

Four changes, in order of how much they bought:

1. **Rank-limited level lines.** Lines are no longer created at the pivot. A pass at the end of the
   script picks the N nearest unmitigated pools per side (measured against `close`), creates the
   line only for those, and deletes any line whose level fell out of the set — so the chart holds
   `2·N` objects regardless of chart length, timeframe, or how many pivots the model is carrying.
   The arrays (`lvPx`/`lvBar`/`lvSide`/`lvSt`) are untouched, so the *model* still sees everything:
   visibility was decoupled from state, which is the correct split and the one this script had not
   made. Selection is `O(n·N)` scalar work plus at most a couple of object ops per bar; `N` and an
   ATR-distance cap are inputs (0 = derive from density).
   *Why the naive version is wrong:* extending only the nearest level from every historical bar
   still yields ~4 lines per bar × hundreds of bars, i.e. spaghetti plus a blown object budget. The
   lines must be *created and destroyed* by rank, not styled by rank.
2. **Boxes with a lifespan.** Every `box.new` carried `extend = extend.right` *and* a per-bar
   `box.set_right(bx, bar_index + 6)`; the extend won, so both the update and the intent were
   defeated. Dropped the extend at all five sites; a box now tracks the right edge only while the
   array is still live (`gSt ≤ 1` within `2·zWin`, OB untouched and within it) and is deleted the bar
   it stops being tradable, under `trimObj = viz != "Full"`. History therefore clears itself instead
   of accreting pale stripes.
3. **Density as one switch** (`Minimal` / `Clean` / `Full`) plus `Pools drawn per side` and an ATR
   reach filter. `showDash`/`btShow` changed type from `bool` to `input.string` — the labels and
   groups survived, and the boolean read sites became `!= "Off"`.
4. **Panels that show only what they hold.** Cells paint their own `bgcolor`, `border_width = 0`,
   `frame_width = 0`: an unused row is invisible, so a 4-row panel is 4 rows tall. Text colours are
   an opaque palette (`txW/txD/txG/txR/txA`) separate from the user's chart colours — alpha belongs on
   backgrounds only. Rows are written through `f_jrow2`/`f_jrow3` with a **row cursor**, which is
   what makes a skipped row collapse instead of leaving a gap; a table created with the max size and
   a cursor is simpler and safer than resizing `table.new` per mode, and inputs re-run the script
   anyway so no stale cells survive a mode change.

Method note for whoever audits this next: the two `table.new` sizes (4×9, 6×13) are still literal
`const int`s. `table.new`'s `columns`/`rows` accept const→simple, so a ternary over
`input.string` is legal, but deriving them from anything series-qualified (`array.size()`) is not —
do not "improve" this into a dynamically sized table.

Verification, same seven checks as §5–§6: `pyne check` OK · `pyne run --bars 600/1500` OK ·
`pinescope` (20 functions; still exactly two stateful ones, `f_dispAt` and `f_frame`) CLEAN ·
`pinetuple` CLEAN · `pinetype` CLEAN (326 typed globals) · `pineaudit` CLEAN (the new nested
`for k` / `for i` selection loops carry the two-sided clamp on the size-derived bound; the
`k`-loop indexes nothing) · journal lockstep re-counted 13/13. `hideSpent` is now unreachable below
Full density (a spent pool has no line to keep), which its tooltip says.

---

## 9. v2.3 — the chain could not complete, and nothing said so

The user's report was *"I want setups to be forming on my chart"* + *"0 data in the journal"*. Both
had one cause, and it was not the strictness of the gates.

### 9a. Six variables without `var`

```pine
int   raidSide = 0      //  → var int   raidSide = 0
float raidPx   = 0.0    //  → var float raidPx   = 0.0
int   raidBar  = -1     //  → var int   raidBar  = -1
int   brokeSide= 0      //  → var …
float brokePx  = 0.0
int   brokeBar = -1
```

A non-`var` global is re-initialised on every bar. The level loop sets `raidBar := bar_index` when a
pool is raided; the candidate block, which runs on the bar where *structure breaks*, copies it into
`pRaidBar`. Those are different bars — that is what a raid-then-shift **is** — so `pRaidBar` was
always `-1`, `gSweep` and `gShift` could never both hold, `gHold` was false, and no setup could arm
while `needSweep` was on (it is on by default, correctly). The journal therefore had nothing to
record: `0 trades` was not a small sample, it was an empty one.

Evidence in the user's own screenshot, before it was diagnosable: a chart that did show a raid read
`RAID BSL 0b`. A liquidity model whose sweep is always zero bars old is not finding simultaneous
events; it is reading a variable that was reset that very bar. The fix is the six `var`s; the
`RAID`/`SHIFT` cells now age out (`> sweepWin + 2` bars → `none`) so the reset can never masquerade
as a fresh raid again.

Note the shape of the bug: every *individual* stage was correct, the arrays were balanced, the
tables in range, the syntax legal — `check`, `lint`, bounds and scope all passed for three rounds.
It is invisible to any static rule, and it is invisible to a reader who checks each block in
isolation. The general lesson for this file: **any cross-bar hand-off between blocks must be
`var`, and any panel that prints an age (`Nb`) is a lie detector for exactly this class** — so keep
printing ages, and read them.

### 9b. `ta.pivothigh(swLenF, swLenF)`

Documented v6 forms are `ta.pivothigh()`, `ta.pivothigh(len)` and `ta.pivothigh(source, left, right)`;
the two-numeric form is not one of them. TradingView resolves it as (left, right) on `high`/`low`
(hence the level lines that did appear), while the pynescript reference implementation binds the
first argument to `source` → `ta.pivothigh(10, 10)` = pivots of the constant 10 = `na` forever, and
the whole indicator runs with empty level arrays. Both readings can't be right, so the call now names
its source. Any ambiguity a *second* implementation resolves differently is a defect even when the
primary target tolerates it.

### 9c. Gate vs score, and the funnel

`Require HTF alignment` (hard veto) double-charged the same fact that the confluence score already
pays for, so it became `HTF alignment = Off | Soft | Veto` (default Soft) alongside
`Killzone = Off | Score only | Veto` (default Veto), `Sweep gate = Off | Any raid | Opposite raid`
(default Any raid, the model's own wording), and `Max risk (ATR)` replacing a hard-coded 4.0.
Principle: **the veto is configurable, the score is always computed from the facts** — otherwise
loosening a gate silently inflates grades and the journal stops being comparable across settings.

To make silence interpretable, `FN[]` counts candidates and each surviving stage since bar 1
(`f_blocked()` names the biggest drop, `f_funnel()` prints the chain into cell tooltips). While
wiring it, a v6 construct was found hostile to the local transpiler: `FN[i] += 1` (augmented
assignment on a direct array index). It is legal Pine — TradingView compiles it — but it pushed
`pyne run` into a compile path that then died on unrelated string content, so the counters use
`array.set(FN, i, array.get(FN, i) + 1)` like the rest of the file. Consistency with the file's own
idiom is also what keeps the toolchain gates usable.

### 9d. What the reference runtime cannot verify (recorded so the next session does not re-derive it)

* **`ta.pivothigh` / `ta.pivotlow` return `na` on every bar** in pynescript 0.6.8 (500/500 bars with
  real ranges and 333 up-bars confirm the data is fine). So the sandbox cannot exercise the pivot →
  level → raid → break chain end-to-end; measuring signal rates needs a hand-rolled pivot stub
  (`high[swLenF] == ta.highest(high, 2*swLenF+1)[swLenF]`), which is what the funnel numbers quoted
  above were produced with. Do not "fix" the script's logic from a runtime signal count — the runtime
  is the limited party here.
* **The emitter rejects long string literals** (it truncates the generated line, then fails its own
  parse with `token recognition error at: ';'`). The deliverable has ~600-character tooltips, which
  TradingView accepts. Execution gate therefore runs on a copy whose strings are truncated to 100
  chars: `/tmp`-style prep is in this file's history — code identical, literals shortened, and the
  copy runs clean at 600/1200/2000 bars.
* **`barstate.isconfirmed` is true on all bars and `islast` once** in that runtime (probed), so
  confirmed-gated blocks *do* run there; the earlier suspicion that the runtime skips them was wrong.
* Files outside the repo are not durable: `/home/user/venv`, the v6 reference clones and the AST
  checkers were gone after a sandbox reset. So `tools/pine-validate.py` now lives **in the repo** —
  LOOP-CLAMP / TABLE-CELL / ARR-LEN with a `--selftest` control that must fire (it caught two defects
  in the checker itself during this pass: a lower-bound test that only accepted `< 0` and so flagged
  the journal loop's correct `i < firstIdx` clamp, and a lockstep rule that flagged every file because
  counting push/pop *call sites* proves nothing → deleted rather than kept as decoration).
* Toolchain relocation: the Pine tooling moved `hoox-dev` → `hoox-sh` (`pip install
  git+https://github.com/hoox-sh/pyne.git`), and PyPI's `pynescript 0.3.0` is a stub — install from
  git. Rebuild: `python3 -m venv /home/user/venv && /home/user/venv/bin/pip install -q numpy numba
  "git+https://github.com/hoox-sh/pyne.git"`.

## 10. Overlay build (tools/archive/mx-context-overlay.pine) — two more emitter limits, one of them a bug class

Written against the same gates as v2: `pyne check` OK, `tools/pine-validate.py` CLEAN (selftest fires),
`pyne lint` 0 errors / 58×C002 length warnings, `pyne run` OK at 300 and 900 bars.

Two reference-runtime findings that generalise past this file:

1. **`request.security` works, tuples and all** — but an **int element in a security tuple came back
   `0`** while the float elements came through. Probed with `close[1]` (249.0 ✓), `[close[1], high[1]]`
   (249.0 ✓) and `bar_index[1]` (0 ✗). So a `bar_index` sentinel inside a security tuple is *parseable
   but not portable*: detect a new HTF array by value change against remembered state instead, which is
   what the file does now (separate memory per side, reset while the slot reads `na`, so a gap that
   reappears at an identical price still registers).
2. **Array element assignment `arr[i] := value` breaks their numeric path**, with a misleading
   `TypingError ... numba_cum_inc ... Cannot determine Numba type of <class 'dict'>`. Rewriting all 13
   sites to `array.set(arr, i, value)` fixed it. TradingView accepts both forms — so this is an
   emitter quirk, not a Pine error, and `pyne check` never flagged it. It only surfaced once a *plumbing*
   run actually pushed elements (see below). **Rule for both files: `array.set` for writes, `arr[i]`
   sugar for reads only.** v2 was audited for the same class and is clean (0 matches for `^\s+\w+\[(i|j|k|n)\] :=`).
   My `pine-validate.py` does NOT check this yet — it is a one-line rule if we ever hit it again.

**The synthetic bars in that runtime are perfectly contiguous: `low > high[1]` is never true in 300
bars, so no 3-bar FVG can exist there at all**, and `ta.pivothigh` returns `na` (already known). That
means `arrs=0 / pools=0` in a straight run proves nothing about the model. To get *some* execution
proof anyway, the gate copy is built with two shims — gap test widened to `close[1] > close[3]` and
pivots replaced by a `ta.highest(high,5)` equality test — so the registry lifecycle actually runs.
With the shims: `arrs` settles at exactly `arrKeep * 2 = 12` and `pools` at `poolKeep * 2 = 20`, i.e.
push, dedup, mitigation walk, expiry, `while ... > cap` trim and the box/line/label delete-on-pop paths
all execute and the caps hold. **This is a plumbing test, not a signal test**: it says the lifecycle is
sound, not that a 4H array was found on Tuesday. One further shim trap for whoever rebuilds this:
`0.9 * ta.atr(14)` *inside* a `request.security` expression makes their numba compile fail outright —
put `ta.*` calls at global scope, never inside the security expression.

Same lesson as §9b, restated because it bit twice: a script whose arrays stay empty and a script whose
arrays are broken both read as an empty chart on TradingView. The `BLOCKED BY` row in v2 and the
`Defects` row here exist so the two are distinguishable from the chart, without a debugger.

## 11. The compiler round (2026-10-09): the gate was too weak, and 68 problems were behind it

The user loaded both scripts and TradingView rejected them: **63 errors + 1 warning on the overlay,
5 errors + 5 warnings on v2** — after every gate I was running had said OK. So the gate order was
wrong, not just the code.

**What changed permanently: `tools/pine-lint.sh` is now the FIRST gate.** It clones and builds
`github.com/folknor/pine-tools` (an open-source Pine v6 language service whose diagnostics reproduce
TradingView's wording, including the `CE10123`/`CE10272` codes) and runs it over the files. `pyne
check` from pynescript is a *parse* front-end: it validated all 63 of those lines and passed. The
order is now `pine-lint.sh` → `pine-validate.py` → `pyne check` → `pyne run`, and "clean" only ever
means clean-as-compiled (see G009/G010 in §5 and below).

### The bug that produced 62 of the 63: collection indexing sugar inside a block

`arr[i]` on an array is **legal at column 0 and silently wrong one indent deeper**. Probed against
the language service, both directions, because my earlier note in this file claimed the opposite:

| shape | verdict |
|---|---|
| `v = a[0]` at global scope | **clean** |
| `s := s + a[j]` inside a global `for` | **CE10123** `cannot apply 'operator +' … array<float> vs const float` |
| `s = a[0] * 2` inside a global `if` | **CE10123** |
| `a[j]` inside a UDF, `a` being a global | **CE10123** — this is what the user's editor reported |
| same UDF with the array **passed as a parameter** | **clean** |

Mechanism as far as it is knowable: inside a local scope the name resolves to the *series of the
collection*, not the element, so every consumer of it is a type error. The reference (v6 manual)
does not document the asymmetry — same class as gotcha G002 ("the reference underdocuments accepted
types"), and the reason this file keeps probe tables instead of quoting docs.

Why it survived: v2 never used the sugar (99 `array.get` calls, 0 offending reads) so the pattern
looked already-settled; my notes even recorded "v2 uses `px[i]` reads ✓ proven", which was **wrong** —
those are `high[k]`/`low[k]`, the *historical reference* operator on built-in series, a different
feature that happens to look identical. **Rule for both files: `array.get`/`array.set` inside any
block; sugar at column 0 only if you must, and never for a collection.** `pine-validate.py` now
enforces it (COLL-SUGAR), and the overlay's 72 read sites were converted mechanically — the fix that
also removed the 62 errors and left the file clean.

### The other classes, each one a whole-file sweep rather than a spot fix

* **FORWARD-REF** — `group=grpR` on v2 line 83 while `grpR` was declared on line 91: *a global is
  visible only after its declaration line, including from inside functions*. One error in the editor,
  but it cascades. All ten group labels are now declared in one block directly under `indicator()`
  with a comment at each original site saying why.
* **ARITY** — v2's `f_jrow2(table, row, l1, v1, c1, p1, l2, v2, c2, p2)` had a call site passing 6
  args (the BLOCKED BY row): "No value assigned to the 'l2' parameter" ×4. v6 user functions have no
  optional parameters. The call now fills the row's right-hand pair with a real cell — `CANDIDATES`
  and the funnel's stage-0 count — which is also the cell that distinguishes "the gates rejected
  everything" from "the model never saw a candidate", the §9b distinction this file keeps making.
* **SHADOW** — v2's journal block declared `int jr = 0` over the global `var float[] jr` (per-trade
  returns). Renamed to `jrow`; the rename then *broke* line 1409 (`str.tostring(jr + 1)` → "operator
  + with array<float>"), which is the proof the shadow was load-bearing: that cell was reading the
  row cursor and would have kept reading it while the returns array stayed out of reach. Any future
  `jr` inside that block is now impossible to confuse.
* **TYPO** — `barstate.is_last` does not exist; `barstate.islast` does. Caught by a narrow denylist,
  not an allowlist: an allowlist written from memory of the spec flags valid code, which is the other
  way a checker becomes decoration.
* **CONDITIONAL_SERIES** — `ta.atr(14)` called twice with one call inside a ternary (`unit =` in the
  overlay, plus v1 sites) is a series-consistency warning: a `ta.*` call only advances on the bars
  that evaluate it. Now one call, then a plain comparison on the stored value.
* **DEAD CONTROLS** (v1 files) — `show_normal_cisd` was an input nothing read: a checkbox that does
  nothing is worse than no checkbox, so it is gone. Four dead tuple slots (`coreUp0`, `brkCoreUp`, …)
  became `_`, which v6 accepts and which documents "deliberately unused" instead of hiding it.
* **REPAINTING_SECURITY** (v1 files) — `request.security(syminfo.tickerid, htf_tf, close)` reads the
  *forming* HTF bar: history settles, realtime wobbles. Now `close[1]` + `lookahead = barmerge.lookahead_on`,
  i.e. v2's form. v1 is superseded, but a file in `tools/` is a file someone will load.

### Checker calibration, because a rule that fires on everything is the same failure as one that fires on nothing

`pine-validate.py` went from 3 rules to 8 (LOOP-CLAMP, TABLE-CELL, ARR-LEN, COLL-SUGAR ×2 cases,
FORWARD-REF, ARITY, SHADOW ×2 cases, TYPO) with `--selftest` requiring the exact counts, so the
control cannot quietly stop firing. Its first run on the *fixed* files produced **17 findings, all of
them checker defects**, and the honest reading is what mattered: 7 were `for j = …` headers taken for
global declarations, 7 were `if x == y` taken for declarations of `x`, and 3 were names inside
trailing comments and string literals (a tooltip reading "the delivery plot" fired FORWARD-REF for
the global `delivery`). Fixed at the source — blank strings before cutting comments, ignore
control-word heads, require `=` not `==`. Net: **selftest PASS, 0 findings on all four scripts, and
the two rules it did *not* catch are the ones I now document as needing the real compiler.**

### Gate results for this round (all re-run after the edits, not before)

`pine-lint.sh tools/*.pine` → **clean ×4** · `pine-validate.py` → selftest PASS, **0 findings ×4** ·
`pyne check tools/*.pine` → **4/4 OK** · `pyne run` on the gate copies → v2 OK at 600 and 1200 bars;
overlay (plumbing-shim copy) OK at 600 and 1200 with `arrs = 12` and `pools = 20`, i.e. exactly
`arrKeep·2` and `poolKeep·2`, so push → dedup → mitigate → expire → trim → object-delete still holds
its caps after 72 read rewrites. `tools/lint.py` on the corpus → 287 pages, 0 problems.

Rebuild recipe if the caches are gone: `python3 -m venv /home/user/venv && /home/user/venv/bin/pip
install -q numpy numba "git+https://github.com/hoox-sh/pyne.git"` and `bash tools/pine-lint.sh
tools/*.pine` (it clones/builds pine-tools itself; pnpm 9 needs `pnpm-workspace.yaml` moved aside,
which the script does).

## 12. The optimisation round (2026-10-09): five defects a live chart showed that the compiler could not

Both scripts compiled, ran and journalled. Then a 5m gold screenshot showed five things no type
checker can see, because they are not syntax errors — they are *semantic* ones. Recorded as the
defect, the fix, and how it was measured.

| # | defect, as seen | why the compiler could not see it | fix |
|---|---|---|---|
| 1 | The overlay's panel and v2's dashboard were both `position.top_right` and overprinted each other; `no data / FVG` bled through the `Bias` block. | Two independent scripts, each valid on its own. TV has no cross-script layout concept. | Overlay panel moved to `position.bottom_right`, and the row count halved by carrying two checkpoints per row (4×7 instead of 2×11). |
| 2 | FVG boxes were walls hundreds of bars wide, and spent ones were drawn with the same weight as live ones. | `box.new(bar_index-3 … bar_index+6)` then `box.set_right(...)` per bar: the **left edge is the creation-time one** and is never advanced, so an array keeps a stripe across its whole life. | `box.set_left(max(born, bar_index - arrSpan))` every bar (span 60/150/320 by Density), and a spent array is now **deleted** rather than relabelled `inv` — an inverted array is history, not a draw on liquidity. |
| 3 | `Passed 5/7 A-` printed on a chart whose only defect line read `no FVG delivery`, with SMT off. | `cpSmt = not smtOn or ...` — a disabled checkpoint **scores a point**. Perfectly typed, perfectly wrong. | `nTot = 6 + (smtOn and smtHave ? 1 : 0)`, SMT contributes to the numerator only when counted, grade cut on the fraction of *enabled* checkpoints. |
| 4 | Seven visual micro-knobs (`arrKeep/arrShow/poolKeep/poolShow/showAnc/showPd/dashOn`) that the user was already collapsing mentally into one switch. | Inputs are free to the compiler; clutter is a human cost. | One `Density` input (Minimal/Normal/Full) deriving all of them; registry bounds became internal constants with a comment saying why they are not inputs. 34 inputs → 28. |
| 5 | The overlay counted `CANDIDATES 286` in its own table **and** v2's journal printed `CANDIDATES / ARMED / FILLED` again. | Duplicated information is not an error. | v2's journal is trade outcomes only now (row deleted, `table.new` 6×14 → 6×12); the dash's right pair became the funnel tail `286 → 2 → 2`, and `BLOCKED BY` names the input to turn (`killzone veto 286 to 12 · kzGate`). |

Defect 3 was the one that had been lying to the read for as long as the panel existed. Defects 1, 2
and 5 are the reason the chart was unreadable rather than merely wrong.

### The scoring scan was reading last bar's state, and merging the loops fixed it as a side effect

The overlay used to scan the registry twice per bar: once for delivery/held (feeding bias and the
grade), once for mitigation + drawing. The scoring scan read `aSt` **before** that bar's mitigation
was applied, so an array closed through on this bar still counted as live context for one bar. One
loop cannot be out of order, and the merge is also the −20 %: fresh-after-expiry is now the same
predicate as "standing", so two conditions collapsed into one.

The obstacle scan (`runway`) was moved after the merged loop for the same reason — counted against the
pre-mitigation registry it treated an array that died this bar as something in the way.

### Measured, and the conditions on the number

`python3 tools/pine-gate-run.py` (now **in the repo**, because verification tooling that lives in
`/tmp` does not survive a sandbox reset and is therefore not verification). It builds a runnable copy
and executes it under hoox-pyne at `--bars 1200`, best of 3, reading the runtime's own `elapsed_ms`
(wall clock is dominated by interpreter + Numba startup).

```
overlay, pre-patch copy, same shims   854 ms   823 ms   registry pinned: arrs=12 (== the cap)
overlay, build 1.1                    683 ms   684 ms   arrs 0-10, inverted=1187 spends
v2, pre-patch                        1257 ms
v2, build 2.5                        1060 ms
```

−20 % on the overlay is the number I stand on (same builder path on both sides after re-shimming,
repeatable to ±2 ms). v2's 15 % is indicative only: its pre-patch copy was built by last round's
ad-hoc shortening, so its tooltip strings are not byte-identical, and v2's only hot-path change is
six fewer `table.cell` writes per closed bar. Neither figure says anything about signal rate.

### The trap this round, which is worth keeping

Forcing the object-lifecycle test exposed a failure mode in my own harness. With the real gap test
(`low[1] > high[3]`) on pyne's **contiguous** synthetic bars, no gap ever forms: the run came back
`arrs=0 inverted=0`, exit 0 — a **clean pass from a script whose entire changed branch never
executed**. Two things fixed that, and both belong in any future harness:

1. the builder injects a *fabricated* 9-point gap (`close[1] > close[3] ? close[1] + 9.0 : na`) into
   the security tuples so the registry actually fills;
2. and it nudges the close-through test by one ATR **in the runnable copy only**, so the
   delete-on-spend branch executes (1187 spends). That is a plumbing test — does removal, `box.delete`
   and the index shift survive — not a claim about how often real charts invert an array.

Also learned the hard way in the same script: string-matching pyne's JSON with `"(\w+)":\s*\{[^}]*"last"`
matched the outer `plots` key and reported the first plot for every name. Numbers from that parser
were wrong, and `parse()` now uses `json.loads`. A checker whose output is misread is worse than none
because it is trusted.

### Gate order, unchanged, and what "clean" still does not cover

`bash tools/pine-lint.sh tools/*.pine` → `python3 tools/pine-validate.py` (+ `--selftest`, 10 control
findings, all fired) → `/home/user/venv/bin/pyne check tools/*.pine` (4/4 OK) →
`python3 tools/pine-gate-run.py tools/*.pine`. Clean-as-compiled: G009 (editor-only argument gates on
`request.*`) and G010 (runtime errors that surface only on the chart legend) still apply, and neither
checker can see a table collision, an unbounded box, or a checkpoint that awards itself a point.

## 13. v1 as the working file again (2026-10-10): the iFVG and time-of-day build

The pasted v1 became the target again, so the file that had been "the audit baseline, left as
received" had to stop being one: nine defects were listed against it, all of them things a compiler
cannot see, and the file now carries the machinery its own labels promised. `tools/cisd-v1-guide.md`
is the user-facing half; this is the record.

| # | defect in v1 as received | fix | opt-out |
|---|---|---|---|
| 1 | `bull_ifvg` fired when price closed **below** a bullish gap (a bearish event) and drew the *bear* gap's box in green — mirrored wrong on both sides, against `inversion-fvg.md` | the gap a candle closes through, decisively, is the one pushed into the registry, with its own level pair and a role derived from which side broke | `iFVG layer = Off` |
| 2 | one iFVG object per chart load: created only when the list was empty, never invalidated, `while size > 1` trim that could not fire, and a panel row that read ACTIVE from then on | registry per side, capped (`ifvgMax`), expired (`ifvgAge`), deleted when price closes back through the far edge | `Track only` keeps the picture, drops everything else |
| 3 | it flagged the inversion *event* and never modelled the *retest*, so there was no setup to trade | tap of CE/near/far edge + close back on the correct side + one entry per zone, with entry/SL/TP drawn and two new `alertcondition`s | entry lines `Draw entry / stop / target`; alerts `Alert on inverted-zone entries` |
| 4 | one 3-bar cooldown shared by both directions, so at the open it kept ~1 gap in 4 and each side suppressed the other | per-side counters, `Bars between new zones (per side)`, default 1 | set to 3 to reproduce v1 |
| 5 | `disp_ok` (the ratio gate) passes 87.6 % of the time → a free score point; `pd_ok`/`body_ok`/`ifvg_ok` could veto but never score | score composition is now four fixed terms + four optional ones, and the grade divides by the number actually scored | `Score composition` group |
| 6 | the sweep test was `high >= level`, measured 89 % closes-through, and a taken level left the array while its line stayed on the chart forever (default), up to `max_lines_count`, after which TV evicts the oldest objects, live ones included | strict test = wick through **and** close back inside with a wick share floor (`02-liquidity/liquidity-sweep.md`); taken levels are retired into a bounded spent list, dimmed, `line.delete`d past the cap | `Sweep = wick through AND close…` off; `Keep up to N spent levels visible` 0 |
| 7 | `ta.pivothigh(len, len)` detects on `hlc3` while the painted and swept level is `high[len]` / `low[len]` — detector and pool were different objects | sources named: `ta.pivothigh(high, len, len)`, `ta.pivotlow(low, len, len)` | none (a plain bug) |
| 8 | killzones were hour-granular, missing London close and NY PM entirely, no Silver Bullet or macro sub-windows, no 2017 set | `nyMin` minutes-since-NY-midnight + `f_win()`, five killzones, three SB hours, five macro cores, `Killzone set`, `No new signals after`, and the window stamped onto every zone label and alert payload | `Trading window = All day` |
| 9 | the alert omitted the entry/SL/TP it had just drawn; `bearish_sweep`/`bullish_sweep` were dead; the dashboard printed `preset` twice; the whole candle series was re-plotted as a tint gimmick | payload carries grade, `n/m` score, entry, SL, TP, body %, window, preset, ticker; dead vars gone; one preset row; `Overlay painted candles` switch | the last one is the switch |

Also added: the **NY AM opening range** as an optional pool pair with a swept-state readout, its own
two alertconditions, and an `Require an opening-range sweep` gate — deliberately default-off, since
turning it on changes what the script is.

The `strictRatio` input is the audit §1a repair (degenerate walk fails instead of dividing by one
tick; symmetric on both sides) and it is **off by default on purpose**: it edits the model's core
displacement test, and that deserves a comparison of signal counts on real data, not a default flip
inside a plumbing round. `tools/cisd-v1-guide.md` §2 says what to switch on for iFVGs-at-the-open.

### Three things this round got wrong before it got right (kept because they are repeatable)

* `bool f_sweepHi(float lvl) =>` is not a function declaration in Pine — a return-type prefix makes it
  a variable declaration and the parser reports `Undeclared identifier "bool"`. Two of these, and the
  type checker named the line exactly.
* A patch script that asserts *between* edits aborts before its write, so the file is unchanged while
  the next command in the same call reports on it. Two rounds were spent chasing "the replace didn't
  match" when the actual failure was an assert two lines later that tripped on `show_live_ifvgs`
  (my check for leftover `live_ifvgs` matched the legitimate input name) and on my own comment prose,
  which named the deleted identifiers. Assert at the end, on code lines only.
* `if ifvgMode == "Track only" → continue` skipped the *drawing* as well as the entry computation,
  inverting the option's meaning. Semantic switches need to be read against their label, not just
  their syntax.

Measured cost: 553 ms against 390 ms for the file as received, at 1200 bars under the reference
runtime — an upper bound, because the harness has to fabricate gaps on nearly every bar to make the
iFVG paths execute at all (contiguous synthetic bars produce none: the first such run reported
`arrs=0`, exit 0, a clean pass from a script whose new branch never ran). Gates: pine-lint clean,
validator 0 findings (selftest PASS), `pyne check` OK, `pyne run` OK with the gap memory pinned at 8
and inverted zones created and deleted without error.

## 14. The screenshot phase (2026-10-10): the candle-range layer, and the sources that defined its failures

The brief was "new indicators or refining of what's existing to get the right tools", starting from the
seven setup screenshots, with everything optional or toggleable. §11 of `tools/crt-candle-range-study.md`
is the feature record; this section is the verification record.

### What the round actually produced

One layer in the existing file (`grp_crt`, 27 inputs, off by default), not a new script, for the
three reasons in §4 of the study: the cadence matches (a state machine on one anchor candle per day),
the object bill is nine moved objects rather than a per-day allocation, and the core needs no new
`request.security` — the prior-day OHLC ladder, the 5-day ADR and the three-consecutive-close tests were
folded into the `"D"` call the file already made as an 8-value tuple. Verified: `grep -c
request.security` is still 3 across the whole file, and the validator's table/fixed-array census is
unchanged apart from `dash` going 2×14 → 2×16.

### Going to the sources instead of asking

You asked whether I could find the failures myself, and pointed at the X pages. The fetch tool reaches
x.com, so the accounts behind the screenshots were read directly, plus six public explainer pages and
two library pages. The findings that changed the build:

* **The failure definition was already in the corpus, and it is the right one.** `15-sessions/london-session-avoidance.md` is the April-2017 stand-aside list — the same year and session as this model's 01:00 anchor, established in §2 — and it is written as a disqualifier list "before any setup is looked for", with the consequence stated as inverted expectancy rather than reduced expectancy. Nine of its fourteen machine-readable criteria are computable in Pine; three are calendar facts and were left out on purpose.
* **`Time Condition > Price Condition`** (@MadoCRT, 2026-10-08) is why the sweep window is a hard gate with its own switch, and why "no raid before the window closes" is a *counted outcome* (void), not silence.
* **The three-gate stop list** (@SpeculatorFL, 2026-10-01: bias → key level and candle range → confirmation, each ending "No = stop/abandon") is the model's own failure taxonomy, and the top reply under it ("somehow the no always gets negotiated into a yes when you're bored") is why `crtOneShot` exists.
* **The +3RR contradiction resolved itself.** crttrading.com's worked example is 50% of the range (partial, stop to breakeven) *then* the opposite bound, i.e. 1.6–2.8R realised — which is the 2.2R the screenshot's box actually measures. So "+3RR" is a ceiling label. The build defaults to the opposite bound, offers `50% then opposite bound` and `R multiple`, and prints the average R available at the bound so the convention is testable.
* **`Model 1` is not definable from public material** — it is C³ course IP (launching 2026-10-15, "its own logic. Its own rules."). Naming our reconstruction after it would put their claim in our code, so the rules are named for what they do.
* Every source that puts a number on the raw pattern puts it near a coin flip (~45% raw, ~60% with a HTF filter, ~60-65% with killzone + structure shift), and the two most careful say plainly that theirs is **not audited**. LuxAlgo's page is the most honest sentence in the whole literature: "No independent, published study tests it."

### My own errors this round, kept in the record

1. **The §6 spec was structurally impossible.** It had the raid happening *inside* the anchor candle
   against *that candle's* bounds — at 01:30 those bounds are not finished, so there is nothing yet to
   raid. Fixed: candle 1 is the reference (the 4H candle *ending* at the anchor hour), candle 2 is the
   anchor, and the provisional-bounds reading survives only as an option named for the failure it causes.
   A spec I wrote an hour earlier being wrong in its central mechanic is the reason the gate order is
   run even on "just a doc" rounds.
2. **One character, sixteen errors:** a comment line written as `# screenshots name, …` instead of `//`.
   pine-lint localized it to one line; the *class* of it (a stray `#` in a .pine) was then grepped across
   all five files. Nothing else had it.
3. **I ran the un-patched patch.** A fix pass over the new block asserted, died, and therefore applied
   none of its seven corrections — but the same `&&` chain then executed the original patch script, so
   the *uncorrected* block landed in the file. The lesson in §13 ("a heredoc patch that asserts before its
   write leaves the file untouched") had the corollary I had not written down: **never chain the target
   script after a failing correction pass**; check the marker, then run.
4. **Two anchor misses from whitespace.** `bool  crtRangeOk` vs `bool crtRangeOk`, and a wrapped line
   indented by three spaces. Line-number surgery with asserts on *both* ends of the span caught the
   second one before it did damage; the first wasted a cycle.
5. **The forced-on run that would have passed.** With the harness sub for `crtOn = true`, the first
   exercise returned a clean exit, a normal timing and `crtSeen=0`: pyne executes 1-day synthetic bars
   whose clock never advances, so a time-anchored layer can compile, run and prove nothing. `crtTfOk`
   (chart coarser than 4H → layer inert) was doing exactly what it should on that data.

6. **I truncated the audit with my own patch.** `io.open(p,'w').write(io.open(p).read() + AUD)` looks
   like an append and is a clobber: Python evaluates the write target (opening the file, truncating it)
   *before* the read expression runs, so the read returned an empty string and 54 KB of §1–§13 became
   §14 only. Recoverable in one command because the previous round was committed - which is the actual
   control here, not my care: `git checkout -- tools/cisd-audit.md`. Rule for this repo: read into a
   name, then open for writing. Never nest them on the same path.
### The harness change that came out of error 5

`tools/pine-gate-run.py` now has named exercise variants (`EXERCISES` + a shared `FORCE` sub list) and a
**must-fire rule**: a variant that runs without moving its control counters prints `PROBLEM` and exits
non-zero. A smoke test whose branch cannot run is not a pass, and this is the second time in this
directory that a green result came from dead code — so the check is now structural, not a note in a doc.
Two variants ship, both calibrated to fire against the positive control:

```
  fire  exercise crt daily reference              crtSeen=1  crtSwp=1  crtVoid=1  crtEnt=0
  fire  exercise crt intra-anchor accumulator     crtSeen=1  crtSwp=1  crtEnt=1  crtNetR=-1  crtState=5
```

The first covers the daily-reference path and the arm → void transition; the second forces the
provisional accumulator, the immediate-entry trigger, the object creation and mutation, the outcome walk
(stop taken, −1R recorded), the stats and the two new table cells. Stand-aside and the range-size gates
are switched *off* inside the variants and that is deliberate: with no real daily history under pyne they
would reject every bar for the wrong reason, which is not a test of the machine.

### Perf: a claim I made, then withdrew

The first version of this section said the daily-scoping of the 2017 gates took the exercise runs from
10457 ms to 734 ms — a 14× win. It is wrong, and the error is worth keeping in the record because it is
a measurement error, not a code error. The exercises ran with `reps=1`; the timed run takes best of 3.
The ~10 s on every single-repetition run was **Numba compiling the generated module in that process**,
cached afterwards — not script time. Re-running the same build twice put the exercises at 780–940 ms,
and re-running the *timed* run moved it between 670 and 728 ms with no code change at all. So:

* the run-to-run spread of this harness is roughly **±60 ms (~8%)**, which is larger than the 691 → 654
  difference I attributed to the refactor;
* the "14×" was a warm-up artifact, and the harness now uses `reps=3` + min for the exercises too, so
  the same mistake cannot be read out of its output again;
* the 567 ms in §13 is not a valid control either, since the harness has since grown eight probes and
  three exercise builds. The honest statement about this layer's cost is: **at the shipped default the
  file measures 670–730 ms and the layer is not the reason for any visible part of it**; the pre/post
  difference is inside the noise floor, and I am not going to claim a speed-up or a slowdown from it.

The daily-scoping stays for the reason that has nothing to do with perf: the source evaluates these
conditions at midnight, `newNyDay` never fires on a chart shorter than one session (so stand-aside was
silently inert on short intraday charts — a real bug), and a once-a-day evaluation of a once-a-day fact
is just correct. `barstate.isfirst` was already the pattern used elsewhere in this file, so it is a
documented v6 spelling and not a guess at `is_last`.

### The C1/C2/C3 question (2026-10-10, same day, later)

Asked whether the candle-1 / candle-2 / candle-3 sequence was integrated. Auditing it against the code
rather than the notes found one thing integrated loosely, one thing not integrated at all, and **one
real bug**:

* **C1** — integrated, and the reference length is now an input (`Reference candle length (min)`, 240
  for the 4H anchor in the screenshots, 60 for the hourly anchors `21-crt/crt-rules.md` lists). The
  first build hardcoded `1200`/`240` in three places, which silently meant "you cannot use the hourly
  variants at all" — the same class of defect as the audit's earlier fixed-vs-input findings.
* **C2** — integrated twice over: the default judges the acceptance on any bar inside the sweep window
  (the read the screenshots support: entries at 01:30 and "3am entry", hours before C2 closed), and
  `Acceptance is C2's own close` is the textbook variant, which additionally remembers the raid and puts
  the stop behind its **deepest tap** rather than behind whatever bar happened to close back inside.
* **C3** — was only a clock (`Void unless reached within N hours of the anchor open`, where 8 hours from
  a 01:00 anchor is exactly the close of candle 3, so the default encoded the rule by accident rather
  than by construction). Now `Enter only inside C3` makes the delivery candle a real gate. What C3
  often also carries in the literature — a structure shift inside it — is still **not** required by the
  entry, because `cisd` is computed in the CISD core further down the file and a Pine global cannot be
  read before it is defined (the validator's FORWARD-REF class). Wiring that in means moving the CRT
  entry block below the core, which is the one structural change this round deliberately did not make.
* **The bug** — in provisional mode the raid test compared the bar against the running bound that
  already included that bar, so `low < running_low` was unsatisfiable and the option's raid could never
  fire. Fixed by raiding and settling against the bound as it stood *before* the bar (`crtPrevHi` /
  `crtPrevLo`) while the target stays the candle's actual opposite bound. Found only because the third
  exercise variant refused to fire and the must-fire rule would not let that pass as a success.
* To find it, the void branches gained a machine-readable `crtWhyCode` twin of the human note (1 no raid
  before expiry, 2 accepted outside, 3 both bounds, 4 no trigger, 5 two-way C2, 6 C2 closed outside,
  7 filter-rejected at C2, 8 no bound taken, 9 no delivery, 10–12 entry refused: side / tick floor /
  range). The panel keeps the sentence; the harness can only read numbers, and "which void" is the
  difference between a test and a guess.

### Still not verified, said plainly

* The time gates (`crtWinOpen`/`crtWinLen`/`crtDeliverH`) cannot be exercised under pyne at all — they
  are checked statically and need one look on a real chart at 01:00 NY.
* `pipSz` assumes 10 ticks = 1 pip (5-digit FX, 3-digit JPY, 2-digit indices). On a 4-digit feed or a
  crypto pair with a different tick size the 50/40-pip stand-aside thresholds are wrong by 10×; the
  thresholds are the only part of the layer with that assumption.
* Whether any of this is *profitable* is untouched by this round: the counters now make the question
  answerable in a journal, and `crtState` + `crtNetR` on 1200 synthetic bars is plumbing, not a result.

## 15. Timeframe adaptation (2026-10-10): a default I could prove was a no-op, and a feature I withdrew

The question was "does the indicator adapt when I switch timeframes, because I do not want to change
settings per chart". The honest answer before this round was *partly*: everything measured in minutes or
NY hours already did, and every parameter measured in **bars** did not, including a `preset` dropdown that
was a manual, per-chart choice. Both halves are now closed off, plus a maintained matrix
(`tools/settings-by-pair.md`) for the residue no script can decide.

**What the code was actually doing, counted before touching it.** The ladder owned eight values
(`tolerence`, `len`, `min_score_for_best`, `signal_cooldown`, `atr_mult_sl`, `near_atr_mult`,
`max_fvgs_per_side`, `max_obs_per_side`). Outside it sat five bar-count inputs (`expiry_bars`,
`liquidity_lookback`, `clean_after_bars`, `ifvgAge`, `crtObAge`), three windows that were not inputs at all
but literals in the code - FVG freshness 10, order-block freshness 12, the premium/discount range in
`ta.highest(high, 25)` - and nothing connected any of it to the chart.

**The rule shipped.** `preset` gains `Auto from chart` (the new default) plus three coarse tiers, and Auto
selects a tier from `timeframe.in_seconds()` rather than interpolating: the source ladder is *not* linear in
time, so inventing a value between 5min and 15min would have been inventing tuning. Separately,
`scale = 300 / timeframe.in_seconds()` converts each bar-count window to the same duration, `max(3, ...)`
except the premium/discount range at `max(8, ...)`.

Three things worth recording about how that was decided:

* **The default was only safe because it was provably a no-op.** On a 5m chart the scale is exactly 1, so
  every derived window lands on the number the input already carried, and the tier is the one the file
  already defaulted to. "Auto" therefore changes nothing for the chart the model was tuned on, which is the
  whole argument for making it the default instead of hiding it behind a switch. The Custom variant in the
  harness below is the empirical version of the same claim.
* **Scaling is gated on `Custom`, not on `Auto`.** The first version tied both to the same flag, so
  overriding the ladder to `15min` on a 30m chart also restored 30m-chart windows sized like 5m ones -
  two unrelated decisions welded together. Now a named tier moves the ladder only.
* **Floors mark the edge of the trick.** From 1m to 60m the table is duration-exact (expiry 5.0h at every
  one). At 4H and 1D every window collapses onto its floor and means "a few bars", not the reference
  duration; `ifvgAge` at 1m lands exactly on the input's own ceiling of 900. That is why `tools/tf-scale-table.py`
  exists and prints the hours columns: so the drift is visible in the documentation instead of hidden by
  plausible bar counts. The table is generated from the formula, not typed.

**A feature built, checked, and withdrawn.** `htfAuto` was written: the bias timeframe derived from the
chart (<=5m -> 60, 15m -> 240, 30m -> 480, else D), because reading an "HTF" bias off `60` on a daily chart
is not a higher timeframe at all. It passed every check available here - `pine-lint` clean, `pyne check`
clean - since a `simple string` flows into `request.security`'s timeframe argument without complaint. It is
nevertheless reverted, because `request.security`'s timeframe is exactly the kind of argument TradingView
gates in the *editor*, and the README already says clean-as-compiled is not clean-on-TV. The asymmetry
decided it: a small convenience for users on timeframes this file documents as unvalidated, against a failure
mode where the entire script will not paste. `htf_tf` stays manual, with the mapping in its tooltip.

**The harness result that matters more than the milliseconds.** The timed run now defaults to Auto, and on
pyne's synthetic **daily** bars that lands on the most degenerate row of the table: `1D`, scale 0.0035,
everything floored - a useful accident, since the default gate run is now a stress test of the clamp path.
Its registry counts moved from `igaps=8 izones=1` to `igaps=2 izones=2`, which needs saying out loud: that is
the rescaling doing its job on a daily chart, not a regression. The new fourth exercise (`preset Custom`)
runs the identical build with scaling off and returns **exactly** `igaps=8 izones=1`, the pre-change numbers.
Timings across the five runs land 728-898 ms against 728-943 ms before, entirely inside the spread §14
established, so no performance claim of any kind is made here.

**A citation I invented.** `crtMinRiskT`'s tooltip and F9 in the candle-range study both asserted "0.216R
lost after friction, audit §11/§13". While writing the per-pair doc I went to check the number and there is
no such measurement: no friction study exists anywhere in the audit, and neither citation resolved to
anything. Both were rewritten as what they are - arithmetic (10 ticks on a 0.01 feed is 0.10, inside a normal
spread) - and this paragraph is the record. It is the second invented-or-misattributed figure this session has
had to retract, and the pattern is consistent: the fabricated numbers were the ones that supported a design
choice I had already made.

**Two patch-script failures, same class, no damage.** `patch_tf.py` aborted twice before writing: once on an
anchor whose left-hand side an earlier loop in the same script had already renamed (`preset == "30min"` ->
`tier == "30min"`), once on an alert concatenation whose prefix I had paraphrased instead of copied. Because
the script accumulates edits and asserts before its single write, the `.pine` was untouched both times. A
third, self-inflicted: five tooltips were spliced in *after* the closing paren of their `input.*` call
because the helper appended instead of inserting - four errors from a text substitution that "applied
cleanly". Substring surgery on Pine needs the same discipline as the Pine itself: match a whole call, not a
line ending.

## 16. The refinement read (2026-10-12): eight defects, one of them mine, and the class they all belong to

Asked whether anything in the file still needed work, the answer was to read it end to end rather than to
invent features. Eight defects, in the order that matters:

| # | defect | who put it there | how it ships now |
|---|---|---|---|
| 1 | `if tier == "%s"` - the ladder's `3min` rung could never match, so 1m/2m/3m charts selected a tier, printed it on the panel and applied the input values instead of 0.55 / len 8 / cooldown 5 / 0.40 / 2.5 | **me**, in the auto-timeframe round (§15): the rename `preset -> tier` was built with Python `%`-interpolation and one placeholder survived into the file | fixed, and it is a real behaviour change on 1m-3m charts, not behind a switch, because the switch (`preset = Auto`) was already nominally on |
| 2 | `... and (not clockOk or true)` in the iFVG entry gate - a term that cannot fail, so the after-hours cutoff never applied to inverted entries while the code read as if it did | pre-existing | `Apply the after-hours cutoff to inverted entries`, default **on**, one toggle from off |
| 3 | the bear side scored `(scCrt and crtOkBull) + (scCrt and crtOkBear)` and its `sMax` carried both, while the bull side had no reference term and a smaller `sMax` - a bearish signal was paid a point for an armed **bullish** range, the one thing every source calls the largest win-rate killer | pre-existing | one aligned term per side, identical `sMax` on both |
| 4 | one shared label array per pair of directions, indexed by the *other* list's counter: `label.delete(array.get(live_ob_labels, i))` where `i` came from the bull box loop, so deleting a bull order block could delete a bear label, and the two lists drifted apart permanently since the cap loops pop at different rates | pre-existing | four per-side lists, each touched at its own index |
| 5 | `orTapHi` / `orTapLo` fed `alertcondition` while staying true on every bar that kept touching, so one sweep at 5m produced up to 24 notifications across the 09:00-11:00 window; "Once Per Bar Close" does not help, an edge does | pre-existing | fired-latches, reset with the range |
| 6 | the order-block spacer `> 6` was the last unscaled bar count in the file: half an hour at 5m, six hours at 1H, which is how zones stop appearing at all on coarse charts | pre-existing | `f_sc(6)`, i.e. in the §15 scaling machinery |
| 7 | `get_liq_target` read the **live** session accumulators, which include the bar being tested: a long taken inside the Asian session could be aimed at this bar's own high, a line a few ticks away that the trade reaches at once and the panel then counts as a result | pre-existing | prior-session latches taken when a session ends, `Target the finished session's extreme`, default **on** |
| 8 | `crtAnchorLen`'s tooltip said 60 covers the hourly anchors (02:00 / 03:00 / 05:00 / 09:00 / 13:00). The state machine had one anchor per day and a day-long `crtUsedToday` latch, so 60 gave exactly one hourly candle's range, once | **me**, in the §15 tooltip, and the claim was in the study too | `Anchor cadence`: `Once per day` (default, unchanged) or `Every reference candle`, which re-rolls the reference and the state per segment. Tooltip and `tools/crt-candle-range-study.md` §11 corrected rather than defended |

**One class, two ends.** Defect 1 was created by a patch script that built Pine text with `%`
interpolation, and defects 6 and 8 were created by a value that was right in one unit and never converted to
another. So the durable fixes are on both ends: the patch scripts in this session now substitute literal
tokens and assert every anchor before a single write (two `%`-argument miscounts during this round died
exactly there, before touching the file), and `tools/pine-validate.py` grew **TEMPLATE-LEAK** so a leftover
placeholder in shipped code is a build failure rather than a story.

**Three rules, and the controls that keep them honest.** `pine-validate.py` goes from eight rules to eleven:
TAUTOLOGY (`or true` / `and false`, matched on code with strings blanked, because prose about being "always
true" is not a defect), TEMPLATE-LEAK (`%s`, `%d`, `.format(`, single-brace `{...}` - explicitly **not**
`{{ticker}}`, which is TradingView's own alert placeholder syntax and was my first false positive on it), and
LADDER-GAP, which judges an `if/else if` string ladder against the input's `options` in both directions: an
option no branch ever matches, and a rung no option can select. The `>= 3 rungs` floor in LADDER-GAP exists
because the first version accused `crtTgt`'s "Opposite bound" and `crtFri`'s "Off", which are the
`else`-residual options of a one-comparison test, not a dispatch table; a rule whose findings have to be
explained away is a rule nobody runs. Archive files have the three literal-class rules suppressed by policy
- `tools/archive/` is the frozen baseline the reversibility argument in §13 depends on, so the point of
keeping it is that nobody fixes it.

The selftest now refuses to pass on fixture evidence alone: `tools/tests/ladder-bug.control.pine` is the
actual broken rung transcribed out of the shipped file, and `--selftest` fails unless the rules still catch
it (5 findings today: 1 TAUTOLOGY, 1 TEMPLATE-LEAK, 2 unreached options, 1 dead rung). Run against the
pre-fix file it reports the same two defect classes before any of my prose was written - which is the only
kind of checker worth keeping in a repo that has already been fooled twice by a green run over dead code.

**What was verified, and the limit of it.** All four harness exercises return identical counters to the
pre-refine run (`crtWhy=3`; `crtEnt=1 crtState=5 crtNetR=-1`; `crtState=2 crtWhy=10`; Custom `igaps=8
izones=1`), so the six restructurings that were supposed to be behaviour-neutral are behaviour-neutral on
every path the reference runtime can walk, and `crtCadence`'s default leaves the state machine alone. Two
things it cannot certify, said plainly: defects 2, 3 and 7 move numbers on a real chart at exactly the hours
the synthetic run never reaches (`ifvgClock` gates on `stopHour`, `tgtPrior` on session boundaries), and
defect 1 changes 1m-3m behaviour that the reference runtime cannot distinguish from 5m at all, since it runs
1-day bars. The comparison is also now across a tooling change - the venv was rebuilt this turn and `pyne`
is 0.6.9 where §14-§15 measured with 0.6.8, so the 715 ms default figure is not a valid control against any
earlier number in this file, and no timing claim is made.

**What I did not touch, with the reason.** `isAsia`/`isLondon` still measure in hours while everything else
measures in minutes, because those two feed the *target* preference list, whose resolution is already bounded
by the prior-session latch added above; `pipSz`'s "10 ticks = 1 pip" heuristic stays as documented in
`tools/settings-by-pair.md` §3 rather than becoming a guess about every broker; `hide_expired_levels` and
`spentMax` stay separate because they answer different questions (a level past expiry vs a level the day has
used); and `analysis`/`Score` on the panel still reflect the current bar only, which is a display choice with
no signal attached and the kind of thing to change when someone asks, not on a general read.

## 17. The killzone level layer (2026-10-13): what shipped, what the compiler caught, and what the green run does not mean

**The ask, and why I answered it with code.** "okay now what", with every remaining item on the list needing
your chart - the 01:00-02:30 NY watch, the `why-not` reading, the paste. So the queued P1 of
`tools/mx-setups-study.md` §8 was built: session extremes (Asia / London / NY AM / London close / NY PM) plus
the prior day's bounds, projected until taken, with a live → raided-and-held → taken state machine, `bgcolor`
shading of the forming session, two `alertcondition`s, two panel rows, default **off**. P2 - the score and the
gate consuming a level - is not built, and the file says so where a future reader will trip over it.

**Cost to the file, measured rather than remembered.** 158 lines (712-869), 13 inputs, 13 `var` arrays plus 4
scalars, 6 functions, **zero** new `request.security` calls - `pd_high`/`pd_low` ride the daily tuple the 2017
stand-aside list already asks for - and zero new plots. `table.new(..., 2, 18)` is the other real change: the
dashboard grid grew from 16 rows to 18 to make room for rows 15 and 16, which is exactly the sort of edit that
hides a silent collision, and the harness's grid probe reads the rendered table rather than trusting me.

**One deviation from the plan, chosen on purpose.** `kzl_s_*` per-session switches instead of reusing the five
`kz_*` gate flags. `kz_asia` off means "do not signal in Asia"; it does not mean the Asian range is
irrelevant, which is what a London-session trader wants to know. The windows themselves are *not* duplicated:
`kzA`/`kzB` hold the same minute pairs as `wLondon`/`wNyAm`/`wAsiaKz`/`wLonCls`/`wNyPm` (so London and NY AM
still move with `Killzone set`), only the switches are separate. The 20:00-00:00 Asia pooled here is the
gate's Asia and the 2017 list's Asia; the *target* preference list still uses the file's 18:00-02:00
accumulator, and both stay labelled rather than quietly unified.

**Two v6 errors, both semantic, one of them a rule this list did not have:**

    Cannot modify global variable "kzlSeen" in function      (f_kzPush tried to bump the counter)
    Undefined variable 'kzB'                                 (the window-ends array was declared kB)

The first is now rule 8 in §5: a function may read a global and call methods on it, but may not assign to the
binding, so `kzlSeen += 2` lives at the two call sites. The second is my own habit of naming an identifier
from memory instead of reading the region I am patching; it has its own entry in the error lists of at least
three earlier rounds and deserves no further defence. **`pyne check` passed both**, which is worth stating
again because it keeps being the interesting fact: syntax-only validation accepts files the compiler rejects,
so `pine-lint` stays the primary gate in `tools/README.md`.

**The harness.** Four probes (`kzlSeen`, `kzlRaid`, `kzlTake`, `array.size(kzY)` as `kzlLv`) and a sixth
exercise. The study file's prescription was followed and then extended: `kzlOn → true`, `kzlMinBars → 1` (a
one-bar synthetic session would otherwise never clear the span guard) and the alternating-clock sub
`int nyMin = 150 + (bar_index % 2) * 600` - without it pyne's frozen `nyMin = 39` means no session ever
closes and the layer is inert behind a green result. Counters: 1198 levels made, 599 raided and held, 599
taken, registry pinned at exactly `kzlMaxLive = 12`; the cap is verified by the number being pinned, not by
reading the `while` loop. The default run and the five earlier exercises came back with counters **identical**
to build `83d4019`, which is what "off means off" looks like when somebody else has to believe it. That is a
counter comparison only - the venv is 0.6.9, earlier rounds' timings are not controls, and no timing claim is
made.

**The raid branch needed a parameter, not a patch.** First run: `kzlTake = 599`, `kzlRaid = 0`. Not a bug -
the synthetic series trends, so across 1198 tested levels not one ended wick-through-then-close-back-inside,
which is what `sweepStrict` demands of a raid. A zero is precisely what dead code looks like, and the only way
to tell the two apart here was to make the branch reachable: the exercise relaxes `sweepStrict` (a shipped
input, switched the way a user would switch it) and the branch fires 599 times. Widening a *parameter* is
allowed; widening the *logic* - an `or true` - is what TAUTOLOGY exists to catch, and it would have caught this
if I had taken the lazy route.

**A new rule in the harness itself, from the same reflex.** `build()` now returns the exercise subs that
matched no line, and an unmatched sub is a `PROBLEM` with a non-zero exit. Before this, a typo in a variant -
`kzlMinBars` written `kzlMinBarsTypo` - silently downgraded that variant to a second copy of the default run,
and the run still printed `fire` with the *default* counters, i.e. a report on a variant that never existed.
Control: introduce that typo, run, watch it fail. It is the same idea as the must-fire keys, one level up.

**What is not verified, and who has to do it.** Offline, this round: `pine-lint` clean on every `.pine` in
the repo (working file and archive), `pine-validate` CLEAN on the target (with `--selftest` PASS: 14 findings on the synthetic fixture, 5 on
the real control), `pyne check` OK, `pine-gate-run.py` rc=0 with 6/6 exercises firing, `tools/lint.py` 0
problems. Nothing here was compiled by TradingView. The label sitting at the session edge, the `bgcolor`
landing on a live session, rows 15/16 not colliding with the CRT rows in the rendered panel, and PDH/PDL on a
Globex day are things the reference interpreter can reason about but not show. §5's rule-7 headroom figures
predate both added layers and were counted with that round's tooling; the honest version of the claim is that
this layer adds no security call and no plot, which are the two caps that bite on a script this size. And
§9d's standing limit holds: an exercise firing proves the path executes, not that the window is right for your
symbol and feed - which is why step 10 of guide §7 is still unpaid.

## 18. Making the level layer customizable (2026-10-13, second build of the day)

**The request, from a real chart.** The user pasted an MNQ 5m screenshot with `kzlOn` on - hundreds of levels made, a few dozen
raided, the dashes and the panel doing their job - and asked for "fully customizable. colors,
name of zones, positions, etc". The layer had six hard-coded colours, six hard-coded names, five
hard-coded windows, one hard-coded label placement and a `bgcolor` at 35 transparency, which on a 5m chart is
wallpaper. Also one hard-coded panel corner that has nothing to do with killzones and was never anyone's
choice.

**What is now an input** (23 in a `Killzone levels: colours, names, windows` group, plus `Dashboard position`
in `Appearance`): six names, two bound words, six colours, five window strings, live line style and width,
shade transparency, label position, label size, label price. Nothing was renamed or removed; the four
behaviour inputs are untouched, so a saved template from the build this morning still means the same thing.

**Three decisions worth the ink they cost.**

1. *The windows default to empty, not to the times.* `""` means "use the killzone window this file already
   computes", which keeps `kzl_londonWin` and the `wLondon` gate in step **by construction** rather than by
   the user re-typing `02:00-05:00` and getting it subtly wrong. Overriding decouples them, and the tooltip
   says that in the same breath as the format, because the failure mode of a decoupled London is a level you
   trust at a time you did not mean.
2. *Parse it, then refuse it.* `f_kzMins` accepts `HH:MM` or exactly four digits and nothing else, so `9` is
   not 09:00 - it is refused. Being lenient here means a session silently shifted by nine hours, which is a
   number someone will trade. A refusal keeps the default, bumps `kzlBadWin`, and prints `!N window refused`
   in orange on the panel row. `f_kzApplyWin` returns 0/1/2 because a v6 function may not assign a global
   (§5 rule 8, learned four hours ago in §17), so the counters are summed at the call site.
3. *Only the live state is decoration.* `Live level style` styles the live line; raided stays dashed + one
   unit thicker and taken stays dotted grey with the projection cut off, because those two are the state that
   the whole layer exists to expose. A customisable state machine is not a customisable look, it is a way to
   make the information unreadable.

**One default changed that is not behind a switch: the shade transparency, 35 → 88.** The rule in this repo is
that a look-only change may land on as long as it is called out, and this one is called out here, in the
guide's table, and in the input's tooltip. It changes nothing for anyone who has not switched the layer on;
for the two of us who have, the bands go from paint-box to tint. `Session shading transparency` is the
one-line answer if 88 is too faint for a projector.

**Verified how.** `pine-lint` clean - which is worth stating because `input.string` fed into `str.pos`,
`str.replace_all` and `str.substring` is exactly the const-qualifier class that has bitten this file before,
and the compiler checked the qualifiers rather than me guessing them. `pine-validate` CLEAN with
`--selftest` PASS (the LADDER-GAP rule matters here: two new `options=` inputs, `Live level style` and
`Label position`, plus `Dashboard position` with six rungs - all six are compared, so no option is a
button that does nothing). `pyne check` OK. Then the harness grew three probes (`kzlBadWin`, `kzlWinCust`,
`kzlLblTick`) and a seventh exercise that overrides nine of the new inputs at once: `Asia window = "02:30-12:30"`
matched to the substituted clock so `kzlWinCust` can only fire if the parser fed the registry;
`NY AM window = "7 o'clock"` deliberately unreadable, and the exercise's must-fire list requires **both**
`kzlBadWin > 0` **and** `kzlSeen > 0` - a refused input that also killed the session would pass a test with
only the first key, and a validator that swallows errors would pass one with only the second.
`Label position = At the right edge` drove `kzlLblTick` to 8948 label updates, the empty upper-bound word
exercised the no-word label path, `Shade transparency = 0` and `Dashboard position = Bottom left` were
carried through `table.new`. 7/7 exercises fire, and the default run's counters are identical to §17's,
which is the sentence that proves the customization is additive.

**Still the user's, and still honest.** No TradingView compile. Colours, sizes, transparency, label position
and panel corner are *rendered* things: pyne executed the branches and counted the calls, and cannot tell you
whether the tint now reads well over your candle style or whether `tiny` labels survive a laptop at 4H zoom.
The `f_kzTag` wording change moved the alert and panel text from `LNDN high` to `LNDN High` (or to whatever
the words inputs say); if you have alert webhooks keying on the old string, that is the one thing here that
could surprise a machine rather than an eye.

## 19. The context round (2026-10-13, third build of the day)

**How this round started.** Not with a screenshot but with a question: "Other features we should add? Or
other that are not necessary to my trading? Make me a good analysis, then after we're done with this round
of ameliorations, give me the full optimal settings." The analysis separated three buckets — worth adding,
not necessary, and already-present-but-unnecessary-for-this-trader — and the user picked the profile the
settings would be written for: **MNQ multi-timeframe (1m/5m/15m), full day, CISD primary with CRT armed,
core round plus SMT**. Everything in this section is downstream of those four answers; a London-only FX
trader should build a different subset and §19 is not evidence otherwise.

**What the analysis found, in the order it was built.**

1. *The level layer could not be consulted.* §17/§18 built and decorated `grp_kzl`, and nothing in the
   score or gate read it — "swept the Asia high, closed back inside" remained a sentence a human says
   about the chart, not a test the file runs. P2 (`scKzl`, `require_kzl_sweep`, both off) is the §8 plan
   arriving two builds after the drawing, which was the plan: draw first, prove the registry, then let
   it near the grade. The raid latches (`kzlRaidBarHi/Lo`) record the bar and the side at the event site;
   the score reads them inside the liquidity lookback, so a raid ages out on the same clock as any other
   sweep in this file.
2. *The target was ranked, not measured.* `get_liq_target` picked PDH over Asia H over London H by fixed
   priority. On an index chart that aims trades at pools that are not the draw. `tgtMode = "Nearest pool"`
   ranks every live candidate — prior day, sessions, un-taken killzone levels, equal pools, the 18-bar
   swing — by distance. Default stays `Fixed priority`: this changes drawn targets on real trades, so it
   is a choice with the old behaviour as the shipped position, per the standing rule. The settings profile
   (§5 of settings-by-pair) is where `Nearest pool` is actually recommended.
3. *The core kept no record of itself.* CRT counted W/L/net R from its first build; BEST — the signal the
   user takes — counted nothing, so every settings argument in this repository has been, for the core, an
   argument from plausibility. The journal (`grp_jrn`, default on, counting only) follows each BEST entry
   to its drawn TP/SL, stop winning same-bar ties, expiry counted at 0R rather than dropped. It is the
   only default-on item in the round, defended the same way `kzlLblTick` was not: it draws nothing, gates
   nothing, and a record that starts when you remember to enable it starts the day you stop needing it.
4. *Equal extremes were five lines, not one pool.* `grp_eq` clusters pivots within a tick tolerance
   into a single averaged pool with a touch count. Two details worth the record: a candidate's stale
   clock runs from the bar its pivot *confirms*, not the pivot bar — a pivot is `len` bars old when
   first seen, and the first draft expired candidates from their own bar, silently spending that much
   of their life (on 15m, expiry 20 − len 11 = 9 usable bars); and a swept pool leaves the target list
   immediately, because a wicked pool is spent liquidity, not a draw.
5. *The blackout is a clock, and says so.* `grp_news` suppresses BEST around two user-set NY times. Pine
   has no calendar; the honest version of this feature is "08:30 ± 15 on days you say so", and the panel
   reads `NEWS-HALT` while it applies rather than the script merely going quiet.
6. *SMT, as a point and not a layer.* `scSmt` plus one sibling `request.security` (4 calls total now).
   The study's §4 architecture verdict stands — no registry, no drawings, no second state machine. The
   read is swing-window, not pivot-matched, and the guide §9 says that in the same breath as the switch.
   The sibling is fetched even with the point off so that a missing feed is a visible `SMT-NODATA`, a
   small instance of the rule that has governed every layer here: an input that cannot fire must say why.
7. *The opens are reference, not machinery.* 00:00 and 09:30 NY dotted lines, nothing reads them. Cheap,
   and included because a level misremembered is worse than a level drawn.

**What "not necessary" meant, and still means.** The analysis also listed what was refused: a calibrated
letter grade (needs the journal's month first), an in-file HTF FVG registry (the overlay's job, §4 of the
study), breaker/rejection/propulsion block species (vocabulary against an 80-box budget), VWAP and volume
profile (no model in the corpus consumes them; TPO is not honestly expressible in Pine), quarterly-theory
lookbacks at execution timeframe, and ten per-session KZL alert conditions (already refused in §17).
Refusals are part of the build record because "fully featured" is how this file got to 2,000 lines.

**Verification, including the two dead paths found on the way.** `pine-lint` clean, `pine-validate`
CLEAN (the LOOP-CLAMP rule caught seven unguarded forward loops in the first draft of the EQ and target
code — the rule exists for the reverse direction, and it was right in both), `--selftest` PASS, `pyne
check` OK. The gate grew fifteen probes and an eighth exercise (three-phase substituted clock
00:00/04:45/09:30, Custom preset, levels on): `kzlSeen=2396`, `kzlRaid=798` (the score latches execute),
`eqMade=86`, `eqTaken=85`, `newsBlk=400`, `openSets=800`, `smtBull=41`, registry still capped at 12.
Two reference-runtime dead paths were found and handled rather than stepped around: `ta.lowest(x)[1]`
on a security-derived series returns `na` under pyne, so the sibling priors are computed as
`ta.lowest(sibLo[1], n)` — history on the input, then the function — which is also the form that cannot
drift a bar; and pyne produces no pivots at all on synthetic bars, so the exercise substitutes the EQ
*detector condition* and the SMT *sweep condition* with periodic legs, documented in the harness, while
the clustering, averaging, sweep, retirement and latch arithmetic behind them is shipped code. What
that does not prove: that a real ES/NQ divergence looks like the latch's window read, or that BEST
entries resolve the way the journal counts them — BEST has never fired on synthetic bars, so the
journal's push/resolve branches are compile-verified and loop-executed, and their first real evidence
is the user's chart. The default run's counters are unchanged from §18, which is the neutrality claim
for the whole round.
