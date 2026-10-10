// NOT PINE CODE — this is a markdown guide. Do not paste it into the Pine Editor.
// The script it documents is: tools/cisd-ultimate-balanced.pine  (that file is the code).
// For the v2 line (gates, funnel, journal) see tools/archive/cisd-v2-guide.md.

# CISD Ultimate v1 — the iFVG / open-time build

`cisd-ultimate-balanced.pine` is the script that was pasted into this project at the start. It was
the audit baseline for a round, and it is now the working file again, with the machinery its iFVG
and time-of-day story always needed. v2 and the overlay are set aside, not deleted.

Pristine copy of the file as it arrived (before these edits): `tools/.archive/cisd-ultimate-balanced.v1-pristine.pine`.
It is dot-prefixed so nobody pastes it by accident; it exists so any decision below can be reversed.

## 1. What changed, and why each piece is behind a switch

Nine defects were found by reading the file end to end (the full record is `tools/cisd-audit.md` §13).
Every one that touches *what the script means* is fixed unconditionally, because a switch that
defaults to "wrong" is a trap; everything that adds *behaviour* is opt-in:

| what | switch | default |
|---|---|---|
| iFVG polarity + zone (it drew the opposite side's gap, in the opposite colour) | — | fixed |
| iFVG registry (was: one object ever, never invalidated) | `iFVG layer` | `Track only` |
| iFVG entries: tap the level, close rejecting, one entry per zone | `iFVG layer` | `Track only` → no entries at all |
| entries counted in the score | `iFVG layer` = `Track + score` | off |
| entries required before signalling | `iFVG layer` = `Track + score + gate` | off |
| entry level inside the zone | `Entry level in the inverted zone` | CE (50 %) |
| how decisive the break must be | `Invalidation needs a body of (ATR ×)` | 0.80 |
| minute-accurate windows, 5 killzones, SB hours, 5 macro cores | `Trading window` | `Killzone` |
| public vs 2017 killzone set | `Killzone set` | Public 2022 |
| London close + NY PM windows | their own booleans | off |
| no new signals after hour N | `No new signals after this NY hour` | 16 (off) |
| NY AM opening range as a pool | `Use the 08:00 opening range as a pool` | off |
| entries gated on an opening-range sweep | `Require an opening-range sweep` | off |
| strict sweep (wick through **and** close back inside) | `Sweep = wick through AND close back inside` | **on** |
| minimum wick share of the candle | `Min wick as share of the candle range` | 0.60 |
| repaired displacement ratio (audit §1a) | `Strict displacement ratio` | off |
| score composition: displacement / premium-discount / body % / iFVG | `Score composition` group | disp on, others off |
| spent levels kept visible but bounded (was: leaked forever) | `Keep up to N spent levels visible` | 24 |
| per-side zone cooldown (was: one shared 3-bar counter) | `Bars between new zones (per side)` | 1 |
| painted-candle overlay | `Overlay painted candles in the trend colour` | on |

Fixed with no switch, because they were simply wrong: the pivot detector now runs on `high`/`low`
instead of the default `hlc3` while the level drawn was `high[len]`/`low[len]`; the entry marks are
tracked and retired instead of orphaned; the `iFVG ACTIVE` panel row counts live zones; the alert
message now carries entry/SL/TP/body %/window.

## 2. Recipe: iFVGs at the open, gold or index futures, 5m

```
Timeframe preset          5min
Trading window            Killzone
London open               on        New York AM         on
Mark the Silver Bullet    on        Mark the five macro cores   on
No new signals after      11          (strict NY AM read; 16 = all day)
Use the 08:00 opening range         on     Range length 30     Sweep window 09 → 11
Require an opening-range sweep      on     ← this is the actual filter
iFVG layer                Track + score + gate
Entry level               CE (50 %)       Invalidation body 0.80 ATR
Live inverted zones       2 per side      Inverted zone expiry 180
Show Live FVGs / iFVGs    on              Bars between new zones 1
Sweep strict              on              Score min for BEST 2
```
Why those: `11-silver-bullet/silver-bullet-rules.md` makes the window item 1 of 8 and non-negotiable,
`31-models/ny-am-open-range-model.md` makes the opening range the pool that gets raided in
09:00–11:00, and `02-liquidity/liquidity-sweep.md` is why a touch of a level is not a sweep. What is
left for you is the judgement the script cannot make: whether the HTF day is *for* that direction.

Quieter / afternoon variant: `Trading window = Killzone + Macro`, `London close` + `New York PM` on,
`Use the 08:00 opening range` off, `No new signals after` 16.

## 3. Reading the panel

Rows 0–12, one line each: `Score` (now `n/m`, m = what is actually being scored), `Analysis`
(which zones are live), `Live FVGs`, `Live OBs`, `iFVG` (`2 inverted / 8 gaps` — gaps are the memory
the inversions are computed from), `Prem/Disc`, `HTF Bias`, `Window` (what you filtered on, plus
`+SB` / `+MACRO` when you are inside one), `Ready`, `Preset`, `Open range` (its two levels and which
bound has been taken), `Score parts` (so the grade is auditable at a glance), `iFVG tap` (the entry
level if a zone was tapped on this bar).

## 4. Cost, measured

`python3 tools/pine-gate-run.py tools/cisd-ultimate-balanced.pine` at 1200 bars, best of 3, runtime's
own `elapsed_ms`: **553 ms**, against **390 ms** for the file as it arrived. The new figure is an
upper bound, not a fair one: to make the iFVG code paths execute at all the harness injects a
synthetic gap on nearly every bar and lets `ifvgDisp` fall to 0, so the engine is running far harder
than it will on a real chart where `fvTop` is capped at 8 and gaps are not printed every bar. The
object counts are also capped by construction now: ≤ 2 inverted zones per side, ≤ 12 entry labels,
≤ 36 entry lines, ≤ 24 spent levels per side.

Verification that ran on this revision: pine-lint (TV-parity type checker) clean ·
`tools/pine-validate.py` 0 findings with `--selftest` PASS · `pyne check` OK · `pyne run` 1200 bars,
gap memory at its cap, inverted zones created and deleted without error. None of that certifies the
*signals* — see `tools/cisd-audit.md` §9d for what the reference runtime cannot tell you.
