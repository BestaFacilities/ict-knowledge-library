#!/usr/bin/env python3
# NOT PINE - this is a python harness, not indicator code. The Pine you paste into
# TradingView is cisd-ultimate-proper-v2.pine and mx-context-overlay.pine.
#
# Builds a runnable copy of a shipped .pine and executes it under hoox-pyne, then times it.
#
# Why a copy at all: the reference runtime refuses non-ASCII and very long string literals,
# and it has no resampled data on some expressions (ta.pivothigh returns na). The transform is
# therefore: strip non-ASCII, cut long literals, and swap the two calls that this runtime cannot
# service for equivalent chart-TF stand-ins. Nothing else changes, so the array/box/table CODE
# PATHS - the ones that actually break - are the same code being executed.
#
# It is a smoke test and a timer, not a signal oracle: bars are synthetic and contiguous, so
# "0 trades" or "2 trades" here says nothing about the model. The object counts printed by the
# appended plots are the durable part: they prove the registries stay inside their caps.
#
#    python3 tools/pine-gate-run.py tools/archive/mx-context-overlay.pine  # build + run + time
#   python3 tools/pine-gate-run.py --raw /tmp/gate-mx.pine                  # time an existing copy
import json
import re
import subprocess
import sys
import time
from pathlib import Path

PYNE = "/home/user/venv/bin/pyne"
MAXLIT = 96

# per-file text substitutions the runtime needs (regex, replacement)
SHIMS = {
    "mx-context-overlay.pine": [
        (r"^float pivHi = ta\.pivothigh\(.*$",
         "float pivHi = high > ta.highest(high[1], 4) and high == ta.highest(high, 5) ? high : na"),
        (r"^float pivLo = ta\.pivotlow\(.*$",
         "float pivLo = low < ta.lowest(low[1], 4) and low == ta.lowest(low, 5) ? low : na"),
        (r'arrMin\s*=\s*input\.float\([0-9.]+', 'arrMin = input.float(0.0'),
        (r'poolMin\s*=\s*input\.int\([0-9]+', 'poolMin = input.int(2'),
    ],
    "cisd-ultimate-proper-v2.pine": [
        (r"^float hh\b = ta\.pivothigh\(.*$",
         "float hh = high == ta.highest(high, 9) ? high : na"),
        (r"^float ll\b = ta\.pivotlow\(.*$",
         "float ll = low == ta.lowest(low, 9) ? low : na"),
    ],
}
# substring substitutions, applied anywhere on a line. The synthetic-gap one is what makes the
# registry fill at all: pyne's bars are contiguous, so a real gap test (low[1] > high[3]) never
# fires and the array code paths would silently go unexercised - a clean run proving nothing.
SUBS = [
    ("low[1] > high[3] ? low[1] : na, low[1] > high[3] ? high[3] : na, "
     "high[1] < low[3] ? low[3] : na, high[1] < low[3] ? high[1] : na",
     "close[1] > close[3] ? close[1] + 9.0 : na, close[1] > close[3] ? close[3] : na, "
     "close[1] < close[3] ? close[3] : na, close[1] < close[3] ? close[1] - 9.0 : na"),
]

# Same reason, different path: with contiguous synthetic bars nothing ever closes a gap through,
# so the "spent array is deleted" branch - the behaviour this version CHANGED - would run zero
# times and a clean exit would prove nothing. Nudging the close-through test by one ATR makes the
# spend fire, which is a plumbing test (does removal + box.delete + index shift survive), not a
# statement about how often real charts invert an array.
# Same trick for v1's own gap test: bull_fvg is low > high[2], which cannot happen on contiguous
# bars either, so without this the whole iFVG engine - the part just written - would be untested.
# The pushed geometry is forced to be a real 9-point gap so the zone logic, the inversion test and
# the "inversion failed, delete it" path all execute.
SUBS += [
    ("if bull_fvg and barstate.isconfirmed", "if (bull_fvg or close[1] > close[3]) and barstate.isconfirmed"),
    ("if bear_fvg and barstate.isconfirmed", "if (bear_fvg or close[1] < close[3]) and barstate.isconfirmed"),
    ("array.unshift(fvTop, low[2])", "array.unshift(fvTop, math.max(low[2], high + 9.0))"),
    ("array.unshift(fvTop, low)", "array.unshift(fvTop, math.max(low, high[2] + 9.0))"),
    ("ifvgDisp  = input.float(0.80,", "ifvgDisp  = input.float(0.0,"),
    ("useOR    = input.bool(false,", "useOR    = input.bool(true,"),
]

SPEND_SUBS = [
    ("if close < array.get(aBot, j)", "if close < array.get(aBot, j) + unit"),
    ("if close > array.get(aTop, j)", "if close > array.get(aTop, j) - unit"),
]

# object-count probes, so the caps are visible in the output
PROBES = {
    "mx-context-overlay.pine": ['plot(array.size(aTop), "arrs")', 'plot(array.size(pPx), "pools")',
                                 'plot(box.count(), "boxes")', 'plot(label.count(), "labels")',
                                 'plot(invSeen, "inverted")'],
    "cisd-ultimate-balanced.pine": ['plot(array.size(ivTop), "izones")', 'plot(array.size(fvTop), "igaps")',
                                    'plot(box.count(), "boxes")', 'plot(line.count(), "lines")', 'plot(crtState, "crtState")', 'plot(crtSeen, "crtSeen")', 'plot(crtSweeps, "crtSwp")', 'plot(crtEntries, "crtEnt")', 'plot(crtVoids, "crtVoid")', 'plot(crtFiltered, "crtFilt")', 'plot(crtNetR, "crtNetR")', 'plot(crtWhyCode, "crtWhy")',
                                    'plot(label.count(), "labels")',
                                    'plot(kzlSeen, "kzlSeen")', 'plot(kzlRaid, "kzlRaid")',
                                    'plot(kzlTake, "kzlTake")', 'plot(array.size(kzY), "kzlLv")',
                                    'plot(kzlBadWin, "kzlBadWin")', 'plot(kzlWinCust, "kzlWinCust")',
                                    'plot(kzlLblTick, "kzlLblTick")',
                                    'plot(jW, "jWins")', 'plot(jL, "jLoss")', 'plot(jExp, "jExp")',
                                    'plot(jNetR, "jNetR")', 'plot(array.size(jDir), "jOpen")',
                                    'plot(eqMade, "eqMade")', 'plot(eqSwept, "eqSwept")',
                                    'plot(eqTaken, "eqTaken")', 'plot(array.size(eqY), "eqPools")',
                                    'plot(smtBullCt, "smtBull")', 'plot(smtBearCt, "smtBear")',
                                    'plot(newsBlkCt, "newsBlk")', 'plot(newsBad, "newsBad")',
                                    'plot(openSets, "openSets")', 'plot(kzlRaidBarHi, "kzlRaidHi")',
                                    'plot(kzlDimCt, "kzlDim")'],
}


def build(src: Path, dst: Path, extra_subs=()):
    """Return the extra_subs that matched no line. A typo in a sub silently turns an exercise into a
    duplicate of the default run, whose 'fire' line would then be reporting on a variant that never
    existed - so an unmatched sub is an error, not a shrug."""
    text = src.read_text(encoding="utf-8")
    text = text.encode("ascii", "ignore").decode("ascii")

    def cut(m):
        s = m.group(1)
        return '"' + (s if len(s) <= MAXLIT else s[:MAXLIT - 2] + "..") + '"'

    lines = [re.sub(r'"([^"\n]*)"', cut, ln) for ln in text.split("\n")]
    shims = SHIMS.get(src.name, [])
    for i, ln in enumerate(lines):
        for pat, rep in shims:
            if re.match(pat, ln):
                lines[i] = re.sub(pat, rep, ln)
                break
        for old, new in (SPEND_SUBS if src.name == "mx-context-overlay.pine" else []):
            if old in lines[i]:
                lines[i] = lines[i].replace(old, new, 1)
        for old, new in SUBS:
            if old in lines[i]:
                lines[i] = lines[i].replace(old, new)
    hit = set()
    for ln_i, ln in enumerate(lines):
        for si, (ex_old, ex_new) in enumerate(extra_subs):
            if ex_old in ln:
                lines[ln_i] = ln.replace(ex_old, ex_new, 1)
                hit.add(si)
                break
    lines += PROBES.get(src.name, []) + [""]
    dst.write_text("\n".join(lines), encoding="utf-8")
    return [old for si, (old, _) in enumerate(extra_subs) if si not in hit]


# Named exercise variants, applied on top of SUBS, one extra run each. They exist because a
# default-off layer on a 1-day synthetic chart can compile, run, time out clean and execute NONE of
# its code: pyne's bars are 86400s, so `hour(time)` never moves and the 4H clock path is inert by
# construction. Each variant therefore has to FIRE, and a variant that runs without firing is
# reported as a failure rather than a pass - that is the whole point of this file.
# pyne runs the script on 1-day synthetic bars whose clock is UTC-ish and drifts with DST, so a
# default-off, time-anchored layer can compile, run, time clean and execute NONE of its code - the
# exact failure this file was written to prevent. Each variant therefore (a) switches the layer on,
# (b) switches off the gates pyne cannot serve, and (c) has to FIRE: a variant that runs without
# firing is reported as a PROBLEM and exits non-zero, because a branch that never ran is not a test.
FORCE = [('crtOn       = input.bool(false,', 'crtOn       = input.bool(true,'),
         ('crtSA       = input.bool(true,', 'crtSA       = input.bool(false,'),
         ('crtTimeHard = input.bool(true,', 'crtTimeHard = input.bool(false,'),
         ('crtRangeMin = input.float(0.30,', 'crtRangeMin = input.float(0.0,'),
         ('crtRangeMax = input.float(1.20,', 'crtRangeMax = input.float(3.0,'),
         ('crtGateCore = input.bool(false,', 'crtGateCore = input.bool(true,'),
         ('scCrt       = input.bool(false,', 'scCrt       = input.bool(true,'),
         # stand-aside needs real daily history and the delivery/bias rules are measured FROM the
         # anchor open: left on, they reject every bar for the wrong reason.
         ('crtDeliverH = input.int(8,', 'crtDeliverH = input.int(0,'),
         ('crtBias     = input.string("HTF bias",', 'crtBias     = input.string("None",'),
         # The tick floor is calibrated to a real 5-digit FX feed; pyne's synthetic prices are a
         # different scale entirely, so the guard (correctly) refuses every entry there. Zeroing it
         # for the exercises is the same kind of unit correction as the gap-geometry subs above.
         ('crtMinRiskT = input.int(10,', 'crtMinRiskT = input.int(0,')]

EXERCISES = {
    "cisd-ultimate-balanced.pine": [
        ("crt daily reference",
         FORCE + [('crtRef      = input.string("Prev 4H candle",',
                   'crtRef      = input.string("Prev daily candle",')],
         ["crtSeen", "crtSwp"]),
        ("crt intra-anchor accumulator",
         FORCE + [('crtRef      = input.string("Prev 4H candle",',
                   'crtRef      = input.string("Intra-anchor (provisional bounds)",'),
                  ('crtAnchorH  = input.int(1,', 'crtAnchorH  = input.int(0,'),
                  ('crtEntry    = input.string("Anchor open retest",',
                   'crtEntry    = input.string("On the close back inside",'),
                  ('bool  crtTfOk  = crtRef', 'bool  crtTfOk  = true or crtRef')],
         ["crtSeen", "crtSwp", "crtEnt"]),
        # The strict C1/C2 read and the C3 entry gate cannot be reached by the two variants above,
        # so they get their own - with the reference length cut to 15 minutes, because the frozen
        # pyne clock sits 39 minutes into the anchor and the C2-close boundary has to be crossable.
        ("crt strict C2 close + C3 entry",
         FORCE + [('crtRef      = input.string("Prev 4H candle",',
                   'crtRef      = input.string("Intra-anchor (provisional bounds)",'),
                  ('crtAnchorH  = input.int(1,', 'crtAnchorH  = input.int(0,'),
                  ('crtAnchorLen= input.int(240,', 'crtAnchorLen= input.int(15,'),
                  ('crtEntry    = input.string("Anchor open retest",',
                   'crtEntry    = input.string("On the close back inside",'),
                  ('bool  crtTfOk  = crtRef', 'bool  crtTfOk  = true or crtRef'),
                  ('crtStrictC2 = input.bool(false,', 'crtStrictC2 = input.bool(true,'),
                  # pyne's clock is frozen, so "the bar that closes C2" never arrives on its own:
                  # settle on a bar index instead. Same branch, reachable boundary.
                  ('            if crtSinceA >= crtLenMin', '            if bar_index > 3'),
                  # ...and the matching half: the anchor has to be BUILT before it can be raided, and
                  # with a frozen clock "inside the anchor candle" and "past the anchor candle" cannot
                  # both be true. Let the accumulator run for the whole series.
                  ('crtRef == "Intra-anchor (provisional bounds)" ? crtSinceA < crtLenMin : false',
                   'crtRef == "Intra-anchor (provisional bounds)" ? true : false'),
                  ('crtC3Only   = input.bool(false,', 'crtC3Only   = input.bool(true,')],
         # crtEnt is NOT required here, and that is deliberate: on pyne's synthetic bars the settle bar
         # tends to close exactly on the running extreme, which trips the "stop must be on the far side
         # of the entry" guard (crtWhy=10) and keeps the setup armed. So this variant proves the strict
         # arm-on-C2-close path AND the entry-refusal path; variant 2 above is what proves entry,
         # objects and the outcome walk. Two controls, four branches between them.
         ["crtSeen", "crtSwp"]),
        # Not a CRT test: the auto tier picker and the rescaled windows are now the shipped default, so
        # they are on in every run above. This one adds the bias-timeframe derivation, whose only safe
        # default is off because it moves signals - and it must actually populate the registries, or a
        # wrong window length would look like a clean run.
        ("preset Custom: the unscaled escape hatch",
         [('"Auto from chart", "Timeframe Preset"', '"Custom", "Timeframe Preset"')],
         ["igaps", "izones"]),
        # The anchor-cadence path (audit s16, defect 8) is a real branch, and it has to be executed, not
        # just compiled. What this run can prove is narrow and is worth stating: the reference runtime sits
        # at a frozen nyMin=39 with 1-day bars, so with the anchor forced to 00:00 the segment index never
        # advances and crtRollNow is only ever evaluated false. That exercises the build condition, the
        # crtRolled gate on crtReady and the reset plumbing; it cannot exercise an actual re-roll, which no
        # synthetic clock here can produce. Do not read this variant as proof that hourly anchors deliver -
        # read it as proof that turning cadence on does not break the machine.
        ("anchor cadence: every reference candle",
         [('crtOn       = input.bool(false,', 'crtOn       = input.bool(true,'),
          ('crtAnchorH  = input.int(1,', 'crtAnchorH  = input.int(0,'),
          ('"Once per day", "Anchor cadence"', '"Every reference candle", "Anchor cadence"'),
          # The guard that made the first attempt of this variant fire nothing: crtTfOk refuses a reference
          # range coarser than 4H, and the reference runtime's chart IS 1-day. Widening the parameter is
          # allowed here; widening the *logic* (an `or true`) is what TEMPLATE-LEAK/TAUTOLOGY exist to stop,
          # and on a real 5m-15m chart the guard passes untouched.
          ('timeframe.in_seconds() <= 14400', 'timeframe.in_seconds() <= 86400')],
         # crtSeen + crtState, deliberately not crtSwp: on a frozen clock the accumulated reference is
         # never raided before the delivery expiry (it reports crtWhy=1, "no raid before the window
         # closed"), which is the correct verdict for that data. Proving the re-roll reaches a verdict is
         # this variant's job; proving a sweep fires belongs to variants 1-3, where it is required.
         ["crtSeen", "crtState"]),
        # The killzone level layer (tools/mx-setups-study.md section 8) is a session-windowed thing, and
        # pyne's clock sits at nyMin=39 forever, so every f_win window is closed and the whole layer would
        # run inert - the exact green-result-from-dead-code failure this file exists to catch. The sub is
        # the documented alternating clock: even bars inside London (150), odd bars outside (750), which
        # rolls a session boundary every other bar so levels get MADE, then tested. kzlMinBars drops to 1
        # because a one-bar synthetic session would otherwise never qualify. What this proves: levels are
        # created, projected, raided and retired, and the caps hold. What it cannot prove: that 02:00-05:00
        # is the right window for your symbol on your feed, or that a real session spans 36 bars.
        ("killzone levels: sessions, raids, mitigation",
         [('kzlOn         = input.bool(false,', 'kzlOn         = input.bool(true,'),
          ('kzlMinBars    = input.int(6,', 'kzlMinBars    = input.int(1,'),
          ('int nyMin = hour(time, "America/New_York") * 60 + minute(time, "America/New_York")',
           'int nyMin = 150 + (bar_index % 2) * 600'),
          # The raid branch needs a wick of sweepWick x range beyond the level and a close back inside.
          # The synthetic series trends hard enough that 0 of 1198 tested levels looked like that - the
          # counter stayed at zero with the code obviously running, which is the same dead-green trap as
          # a dead switch. Relaxing the *parameter* (never the logic) makes the branch fire; the strict
          # default stands on a real chart, where 89% of the hits closed through and are counted as takes.
          ('sweepStrict = input.bool(true,', 'sweepStrict = input.bool(false,')],
         ["kzlSeen", "kzlRaid", "kzlTake"]),
        # The look group (colours, names, windows, label placement, panel position) is not decoration to
        # take on trust: every one of those inputs has a branch, and a branch that never runs is exactly
        # the defect this file was written to catch. Same clock sub as the exercise above, plus three
        # overrides that each prove something different. '02:30-12:30' is a VALID custom window that
        # matches the alternating clock, so kzlWinCust fires only if the parser fed the registry.
        # "7 o'clock" is deliberately unreadable: kzlBadWin must come back non-zero, and kzlSeen must
        # STILL fire, which is the pair that proves a refused window is refused quietly rather than
        # taking the session (or the script) down with it. 'At the right edge' drives kzlLblTick, the
        # one branch with a per-bar cost, and the empty upper-bound word drives the label-text path.
        # A taken level's dotted grey style and a raided one's dashed weight are then re-set on objects
        # built in the user's style, which no counter sees - read that part as 'it ran', not 'it looked right'.
        ("killzone levels: custom windows, look, refused input",
         [('kzlOn         = input.bool(false,', 'kzlOn         = input.bool(true,'),
          ('kzlMinBars    = input.int(6,', 'kzlMinBars    = input.int(1,'),
          ('int nyMin = hour(time, "America/New_York") * 60 + minute(time, "America/New_York")',
           'int nyMin = 150 + (bar_index % 2) * 600'),
          ('kzl_asiaWin   = input.string("",', 'kzl_asiaWin   = input.string("02:30-12:30",'),
          ('kzl_nyamWin   = input.string("",', 'kzl_nyamWin   = input.string("7 o\'clock",'),
          ('kzlLblPos     = input.string("At the session edge",',
           'kzlLblPos     = input.string("At the right edge",'),
          ('kzl_hiWord    = input.string("High",', 'kzl_hiWord    = input.string("",'),
          ('kzlLblPrice   = input.bool(false,', 'kzlLblPrice   = input.bool(true,'),
          ('kzlLineStyle  = input.string("Solid",', 'kzlLineStyle  = input.string("Dotted",'),
          ('kzlShadeTransp = input.int(88,', 'kzlShadeTransp = input.int(0,'),
          ('dashPosIn             = input.string("Top right",',
           'dashPosIn             = input.string("Bottom left",')],
         ["kzlSeen", "kzlWinCust", "kzlBadWin", "kzlLblTick"]),
        # The context round (KZL score/gate, EQ pools, news blackout, opens, SMT latch, journal,
        # nearest target) gets one exercise with a three-phase clock - 00:00 / 04:45 / 09:30 - because
        # that is the only substituted clock that captures BOTH session opens, sits inside London for
        # the level layer, and lands inside a blackout window set to the middle phase. The sibling is
        # blanked to the chart's own symbol: pyne has one synthetic symbol, so this proves the SMT
        # latch executes and counts, and proves nothing about divergence - with one series the sibling
        # IS us, and any 'divergence' it finds is the pivot-vs-window arithmetic, named here so nobody
        # reads the counter as evidence. eqTolT goes to its input ceiling for the same unit reason the
        # CRT tick floor is zeroed above: tolerance is denominated in the synthetic feed's ticks.
        # jWins/jLoss are probed but deliberately NOT must-fire: whether a BEST entry resolves inside
        # 1200 synthetic bars is a property of the synthetic trend, not of the journal's bookkeeping;
        # what this run must prove is that the journal's inputs and the resolution loop execute inside
        # a live script (jOpen is plotted for the same reason).
        ("context round: pools, blackout, opens, SMT latch",
         [('kzlOn         = input.bool(false,', 'kzlOn         = input.bool(true,'),
          ('kzlMinBars    = input.int(6,', 'kzlMinBars    = input.int(1,'),
          ('sweepStrict = input.bool(true,', 'sweepStrict = input.bool(false,'),
          ('int nyMin = hour(time, "America/New_York") * 60 + minute(time, "America/New_York")',
           'int nyMin = (bar_index % 3) * 285'),
          ('scKzl   = input.bool(false,', 'scKzl   = input.bool(true,'),
          ('eqOn       = input.bool(false,', 'eqOn       = input.bool(true,'),
          ('eqTolT     = input.int(10,', 'eqTolT     = input.int(200,'),
          ('newsOn     = input.bool(false,', 'newsOn     = input.bool(true,'),
          ('newsT1     = input.string("08:30",', 'newsT1     = input.string("04:45",'),
          ('openOn     = input.bool(false,', 'openOn     = input.bool(true,'),
          ('scSmt   = input.bool(false,', 'scSmt   = input.bool(true,'),
          ('smtSym     = input.symbol("CME_MINI:ES1!",', 'smtSym     = input.symbol("",'),
          ('tgtMode      = input.string("Fixed priority",', 'tgtMode      = input.string("Nearest pool",'),
          # pyne's synthetic bars produce no pivots at all (ta.pivothigh/pivotlow stay na - the same
          # dead path tools/mx-setups-study.md section 7 records), so the EQ registry would execute
          # zero times behind a green run. The detector CONDITION is substituted for a periodic one;
          # the clustering, averaging, drawing, sweep and retirement code that runs behind it is the
          # shipped code, and the tolerance line goes with it because 'ticks' on the synthetic feed
          # are not a unit anyone chose. On a real chart the pivot condition stands untouched.
          ('if eqOn and not na(pivhigh)', 'if eqOn and bar_index % 7 == 5'),
          ('if eqOn and not na(pivlow)', 'if eqOn and bar_index % 9 == 4'),
          # Same dead path, one layer up: wicked_high/wicked_low are only ever set inside the pivot
          # sweep loops, so the SMT latch's assignment branch is unreachable on synthetic bars. The
          # sweep CONDITION gains a periodic leg (harness only); the sibling comparison it guards -
          # the actual SMT arithmetic - is the shipped code, against the chart's own series, so all
          # this proves is that the latch executes, counts and ages. Divergence itself needs two real
          # symbols and is not claimed anywhere in this run.
          ('if wicked_low and sibLo > sibLoPrior', 'if (wicked_low or bar_index % 29 == 3) and sibLo > sibLoPrior'),
          ('if wicked_high and sibHi < sibHiPrior', 'if (wicked_high or bar_index % 31 == 7) and sibHi < sibHiPrior'),
          ('float tol = eqTolT * syminfo.mintick', 'float tol = 1e9'),
          # A candidate that never gets a second touch expires with the swings; on the reference
          # runtime's daily bars the scaled expiry is 3 bars, so every candidate would die decades
          # (in bar terms) before the substituted detector offers it a partner. Widen the parameter.
          ('expiry_bars            = input.int(60,', 'expiry_bars            = input.int(5000,'),
          ('"Auto from chart", "Timeframe Preset"', '"Custom", "Timeframe Preset"'),
          # pyne resolves literal symbols only; a computed symbol string comes back na, which would
          # make this exercise 'prove' the SMT-NODATA guard instead of the latch. Literal it is.
          ('[sibHi, sibLo] = request.security(smtEffSym, "", [high, low])', '[sibHi, sibLo] = request.security(syminfo.tickerid, "", [high, low])')],
         # smtBull is must-fire; smtBear is probed but not required: the synthetic series trends one
         # way, so a self-sibling confirms every new high and the bearish latch has nothing to catch.
         # Requiring it would be requiring the data to be a different shape, not the code to work.
         ["kzlSeen", "newsBlk", "openSets", "eqMade", "smtBull"]),
        # The declutter round: same alternating clock as the killzone exercises. Taken levels are
        # DELETED on the take bar (kzlDrawTaken off) - which kzlTake already proves executes - and
        # prior-day levels are dimmed exactly once, which only kzlDimCt can prove: kzDayN rolls when
        # the substituted clock wraps from 750 back to 150, so day-0 levels still live must dim on
        # day 1. The compact dashboard and the (default-off) swing-line switch change no counter;
        # they are carried here so the table-renumbering code runs in both shapes somewhere.
        ("declutter: taken deleted, old levels dimmed, compact panel",
         [('kzlOn         = input.bool(false,', 'kzlOn         = input.bool(true,'),
          ('kzlMinBars    = input.int(6,', 'kzlMinBars    = input.int(1,'),
          ('sweepStrict = input.bool(true,', 'sweepStrict = input.bool(false,'),
          ('int nyMin = hour(time, "America/New_York") * 60 + minute(time, "America/New_York")',
           'int nyMin = 150 + (bar_index % 2) * 600'),
          ('kzlDrawTaken  = input.bool(true,', 'kzlDrawTaken  = input.bool(false,'),
          ('dashCompact           = input.bool(false,', 'dashCompact           = input.bool(true,')],
         ["kzlSeen", "kzlTake", "kzlDim"]),
    ],
}

def run_copy(p: Path, bars: int, reps: int = 3):
    """pyne reports elapsed_ms for the script itself, which is the number worth comparing -
    wall clock here is dominated by interpreter and Numba startup."""
    out = []
    for _ in range(reps):
        t0 = time.perf_counter()
        r = subprocess.run([PYNE, "run", "--bars", str(bars), "--json", str(p)],
                           capture_output=True, text=True)
        out.append(((time.perf_counter() - t0) * 1000.0, r.returncode, r.stdout, r.stderr))
    return out


def parse(out: str):
    """elapsed_ms + every plot's last value, read from pyne's own JSON (string-matching the
    nested objects by hand silently matched the wrong keys, which is worse than no number)."""
    ms, plots = None, {}
    try:
        d = json.loads(out)
        ms = d.get("elapsed_ms")
        for k, v in (d.get("plots") or {}).items():
            if isinstance(v.get("last"), (int, float)):
                plots[k] = float(v["last"])
    except (ValueError, AttributeError):
        pass
    grid = re.search(r"'position': '(\w+)', 'columns': (\d+), 'rows': (\d+)", out)
    return (ms, plots, ("%s %sx%s" % (grid.group(1), grid.group(2), grid.group(3))) if grid else "n/a")


def main() -> int:
    raw = "--raw" in sys.argv
    bars, args = 1200, []
    a = sys.argv[1:]
    while a:
        if a[0] == "--raw":
            a.pop(0)
        elif a[0] == "--bars":
            a.pop(0)
            bars = int(a.pop(0))
        elif a[0].startswith("--"):
            a.pop(0)
        else:
            args.append(a.pop(0))
    if not args:
        print(__doc__)
        return 2
    rc_all = 0
    for arg in args:
        src = Path(arg)
        dst = src if raw else Path("/tmp") / ("gate-" + src.stem + ".pine")
        if not raw:
            build(src, dst)
            print("built %s  %d bytes" % (dst.name, dst.stat().st_size))
        runs, fail = [], None
        for wall, rc, out, err in run_copy(dst, bars):
            if rc != 0:
                fail = (rc, out, err)
                break
            ms, plots, grid = parse(out)
            runs.append((ms, wall, plots, grid))
        if fail:
            rc_all = 1
            print("  FAIL rc=%d\n%s\n%s" % (fail[0], fail[1][-1500:], fail[2][-2500:]))
            continue
        ms = min(r[0] for r in runs if r[0])
        counts = "  ".join("%s=%g" % (k, v) for k, v in sorted(runs[0][2].items()))
        print("  ok  script %6.0f ms (wall %6.0f ms best of %d) @ %d bars   %s   table: %s"
              % (ms, min(r[1] for r in runs), len(runs), bars, counts, runs[0][3]))
        for name, extra, must in EXERCISES.get(src.name, []):
            vdst = Path("/tmp") / ("gate-%s.pine" % re.sub(r"\W+", "-", name))
            dead_sub = [] if raw else build(src, vdst, extra)
            if dead_sub:
                rc_all = 1
                print("  PROBLEM exercise %-32s matches no line, so it is the default run and proves nothing:\n          %s"
                      % (name, "\n          ".join(s[:70] for s in dead_sub)))
                continue
            wall, rc, out, err = min(run_copy(vdst, bars, reps=3), key=lambda r: r[0])
            if rc != 0:
                rc_all = 1
                print("  FAIL exercise %s rc=%d\n%s\n%s" % (name, rc, out[-1200:], err[-2000:]))
                continue
            vms, vplots, _ = parse(out)
            vs = "  ".join("%s=%g" % (k, v) for k, v in sorted(vplots.items()))
            dead = [k for k in must if vplots.get(k, 0) <= 0]
            if dead:
                rc_all = 1
                print("  PROBLEM exercise %-32s ran but never fired (%s) - it tests nothing: %s"
                      % (name, ", ".join(dead), vs))
            else:
                print("  fire  exercise %-32s %5.0f ms   %s" % (name, vms or -1, vs))
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
