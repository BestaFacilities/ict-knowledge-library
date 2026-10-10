#!/usr/bin/env python3
"""tf-scale-table.py -- prints the markdown table that tools/settings-by-pair.md quotes, straight from the
formula in tools/cisd-ultimate-balanced.pine. It exists so the table cannot drift from the code:
regenerate it after any change to the tier ladder, the reference values, or the floors, and paste the
output over the marked block.

    python3 tools/tf-scale-table.py

Mirror of the shipped derivation. KEEP IN SYNC with tools/cisd-ultimate-balanced.pine:
  * the `tier` ladder            (thresholds in seconds -> tier name)
  * tfScale = tfAuto ? 300 / tfSec : 1
  * f_sc(v) = max(3, round(v * tfScale))
  * obWin   = tfAuto ? obRefAge : 100000        (only when the order-block window input is 0)
  * pdWin   = max(8, round(25 * tfScale))
  * the reference values it rescales: expiry 60, liqLook 12, cleanAfter 35, ifvg 180, crtOb 12,
    fvgFresh 10, obFresh 12, prem/disc 25  (all of them measured on a 5-minute chart)
If you change one and not the other, this table lies, and the document that quotes it lies with it.

The last two columns are the point of the whole exercise: they show the same settings expressed as
elapsed time, which is what a bar count was always standing in for. Where a row drifts away from the
5m row in hours, a floor is holding it up, and the drift is the honest limit of the extrapolation.
"""
from math import floor

REF = {"expiry": 60, "liqLook": 12, "cleanAfter": 35, "ifvgAge": 180,
       "crtObAge": 12, "fvgFresh": 10, "obFresh": 12, "pdWin": 25}
BASE_SEC = 300          # the timeframe the core was tuned on: 5m
CHARTS = [("1m", 60), ("3m", 180), ("5m", 300), ("15m", 900), ("30m", 1800),
          ("60m", 3600), ("4H", 14400), ("1D", 86400)]
HDR = ["chart", "tier it picks", "scale", "expiry", "liq look", "clean after", "iFVG age",
       "CRT / OB age", "FVG / OB fresh", "prem-disc", "expiry as time", "clean as time"]


def tier(sec):
    if sec <= 180:   return "3min"
    if sec <= 300:   return "5min"
    if sec <= 900:   return "15min"
    if sec <= 1800:  return "30min"
    if sec <= 3900:  return "60min"
    if sec <= 15000: return "240min"
    return "1D"


def pine_round(x):
    """math.round() in Pine rounds half away from zero; Python's round() is banker's rounding. The two
    agree on every cell of the current table, but a changed reference value could land on a .5 tie, so the
    table uses Pine's rule and can never be one bar out by accident."""
    return int(floor(x + 0.5)) if x >= 0 else -int(floor(-x + 0.5))


def f(v, sc, floor=3):
    return max(floor, pine_round(v * sc))


def fmt(x):
    s = ("%.2f" % x if x >= 1 else "%.4f" % x).rstrip("0").rstrip(".")
    return "x1" if s == "1" else "x" + s


def hours(bars, sec):
    h = bars * sec / 3600.0
    return "%.1f h" % h if h < 48 else "%.0f h" % h


def main():
    print("| " + " | ".join(HDR) + " |")
    print("|" + "---|" * len(HDR))
    for lbl, sec in CHARTS:
        sc = float(BASE_SEC) / sec
        e = f(REF["expiry"], sc)
        c = f(REF["cleanAfter"], sc)
        cols = [lbl, "`%s`" % tier(sec), fmt(sc), str(e), str(f(REF["liqLook"], sc)), str(c),
                str(f(REF["ifvgAge"], sc)), str(f(REF["crtObAge"], sc)),
                str(f(REF["fvgFresh"], sc)) + " / " + str(f(REF["obFresh"], sc)),
               str(max(8, f(REF["pdWin"], sc, 8))),
                hours(e, sec), hours(c, sec)]
        print("| " + " | ".join(cols) + " |")


if __name__ == "__main__":
    main()
