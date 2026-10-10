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
                                    'plot(box.count(), "boxes")', 'plot(line.count(), "lines")',
                                    'plot(label.count(), "labels")'],
}


def build(src: Path, dst: Path) -> None:
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
    lines += PROBES.get(src.name, []) + [""]
    dst.write_text("\n".join(lines), encoding="utf-8")


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
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
