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
                                    'plot(label.count(), "labels")'],
}


def build(src: Path, dst: Path, extra_subs=()) -> None:
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
    for ln_i, ln in enumerate(lines):
        for ex_old, ex_new in extra_subs:
            if ex_old in ln:
                lines[ln_i] = ln.replace(ex_old, ex_new, 1)
                break
    lines += PROBES.get(src.name, []) + [""]
    dst.write_text("\n".join(lines), encoding="utf-8")


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
            build(src, vdst, extra)
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
