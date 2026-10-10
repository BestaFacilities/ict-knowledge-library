// ⚠ NOT PINE CODE — this is a study note. The code it proposes going into is
// tools/cisd-ultimate-balanced.pine  (and the archived overlay holds the one module worth lifting).

# The 4H-candle-range / 01:30-sweep breakdowns — inventory and build verdict

**Sent:** 2026-10-10. Seven images: two "TRADE BREAK DOWN" panels (EU = EURUSD, GU = GBPUSD, each with
a 4H panel, a 15m panel and an "Execeution" panel), the two X posts that carry the checklists
(@EU_SNIPER_01, plus a @ONESTrades post naming @SpeculatorFL and @MadoCRT), and two chart close-ups
(EURUSD 15m FXCM, and a wider shot with the 4H candles individually labelled).

**What they are, honestly:** promotional breakdowns of winning trades, drawn after the fact with
hand-placed rectangles. They specify a model very well and validate it not at all — both examples won,
no losers were published, and nothing in the images shows the levels existing before the move. So this
note treats them as a **specification source**, not as evidence.

## 1. The checklists, verbatim

EU Sniper, both posts (GU adds the third line):
> 4H Key + 4H Candle Range
> +3RR
> -WEEKLY MARKET PROFILE
> -Daily Timeframe Directional Bias
> -4H Market Content
> -OLHC/OHLC
> -Key Timing
> -Model 1 & Micro CRT Model 1 Entry

> -Key Timing **01:30** Liquidity sweep
> -Model 1 ENTRY

ONES Trades (EURUSD, +3R):
> Daily Bias alignment. 4h + Daily Key level. **4h 1 AM CRT.** 15m Orderblock. OHLC of the Daily Candle.

Labels visible on the charts: `OB`, `PDH`, `SMT` (on a diagonal dashed line joining two swing points),
`KL`, `TS`, `FR1`, `FRI`, `W OPEN`, and the 4H candles individually tagged `17`, `21`, `1`.

## 2. The one thing that pins the whole model down

The 4H candles are labelled **17, 21, 1**. A 4H ladder running 17:00 → 21:00 → 01:00 is the FX day
anchored at the **17:00 New York** open, so their chart clock is NY and the candles they name are
01:00-NY opens. Two consequences, both checkable:

* "**4h 1 AM CRT**" is the **01:00 NY 4H candle** — its range and its open. Not 01:00 London, not a
  broker-server time.
* "**Key Timing 01:30 liquidity sweep**" is a sweep **30 minutes into that candle's life**. 01:00 NY
  is exactly where `10-killzones/killzone-times-table.md` puts the **April-2017 mentorship London
  killzone** ("the time window begins at 1 a.m., it ends at 5 a.m."), and the macro core that
  precedes it is 00:50–01:10 NY.

So this is not a new doctrine to reconcile against the library: it is the 2017 killzone set, which
`cisd-ultimate-balanced.pine` already carries as a switch (`Killzone set`), applied to a candle-range
reference. Note the tension and record it: `21-crt/crt-rules.md` lists the community CRT hours as
02:00 / 03:00 / 05:00 / 09:00 / 13:00 NY and **no page in the corpus carries an 01:00 or 01:30
sweep anchor**. This variant is earlier than what the library has recorded, and it is the kind of
thing worth an ingest with a real source id rather than an X post.

## 3. Element by element

| element in the images | mechanical content | corpus anchor | already in v1? | buildable in Pine? |
|---|---|---|---|---|
| `4H Key` | the anchor candle's open (and its four prices) as the day's reference level | `04-time-cycles/time-of-day-pivots.md` (time-anchored levels, explicitly "NOT structural pivots") | **no** | yes, free |
| `4H Candle Range` | the anchor candle's high→low, delivered back through on reversal | `21-crt/candle-range-theory.md` | no | yes |
| `Micro CRT` | the same test on one 15m candle adjacent to the sweep | `21-crt/crt-rules.md` | no | yes |
| `Key Timing 01:30 sweep` | wick through a bound and close back inside, inside a clock window | `02-liquidity/liquidity-sweep.md`, `10-killzones/` (2017 set) | **half** — v1 has the 2017 switch and the strict sweep test; it has no "30 min after this candle's open" window | yes |
| `TS` marker | Turtle Soup: failed breakout **and** the sweep landing in a HTF discount/premium array | `20-turtle-soup/turtle-soup.md` | no (v1 records the sweep event, not the failure pattern) | yes |
| `OB` line at 15m | the LTF order block used as the trigger | `07-order-blocks/` | yes, but loose: v1 calls any colour flip an OB (`close>open` after `close[1]<open[1]`) | yes, tighten |
| `OLHC/OHLC` of the daily candle | prior day's open/high/low/close as a four-level ladder | `time-of-day-pivots.md`, `04-time-cycles/filling-the-numbers.md` | **partial** — v1 has `pd_high`/`pd_low` from `"D"`; no PDO/PDC | yes, 1 extra security tuple |
| `W OPEN` line | True Week Open — ICT carries **two**: Sunday open and Monday 00:00 NY | `22-quarterly-theory/true-week-open.md` | no | yes |
| `SMT` diagonal | EUR↔GBP divergence at the paired extremes (the pair IS the comparison, not "smart money technique") | `16-smt-divergence/` | no in v1 — **it exists in the archived overlay** | yes, 1 security call + data entitlement |
| `KL` | "key level", generic | glossary | n/a | n/a |
| `FR1` | **unresolved.** Nothing in the corpus or in these images defines it; my candidates are "first rebalance" or a fib retrace label | none | — | do not guess |
| `+3RR` | fixed 3R target, no graduation | `32-risk-management/`; `15-sessions/twenty-pips-per-day.md` is the counter-example (fixed 20/20, "not graduating it") | yes (`rr_target`, default 2.0) | already |
| `Daily Timeframe Directional Bias` | HTF bias | `25-htf-bias/` | yes (EMA/close test on `htfTf`) | already |
| `4H Market Content` | the 4H PD arrays and pools that give the level meaning | `05-pd-arrays/htf-pd-array-hierarchy`, `25-htf-bias/top-down-analysis.md` | **no** — v1 has a bias test, not an array registry. The archived overlay's registry is exactly this | yes, and it is the expensive one |
| `WEEKLY MARKET PROFILE` | volume/TPO structure: POC, value area high/low for the week | only name-checked in `multi-asset-analysis.md` / `top-down-analysis.md`; no profile page | no | **not honestly** — see §5 |

**One arithmetic check on the +3RR label.** On the EU execution panel the printed prices give an entry
near 1.12280–1.12307, a stop above the 1.12410/1.12450 high, and the green box ending at 1.11998.
That is roughly 13–14 pips of risk against 28–31 pips of reward, i.e. **about 2.2R, not 3R**. Either
the green rectangle is a 3R *projection* that was not run to, or the entry was taken from a level I
cannot resolve from a screenshot. Worth knowing before copying the target convention: the label and
the levels in the same image do not agree.

## 4. Verdict: extend v1 with a reference-candle layer, do not fork a new script

Three reasons, in order of weight:

1. **The cadence matches.** A candle-range model is a state machine on the *current day's anchor
   candle* — capture it once, watch one bound, fire once. v1 is already that shape (per-bar facts,
   bounded registries, no per-bar allocation). The archived overlay needed a separate script because a
   *registry of HTF arrays across three slots* is a different cadence and a different object profile;
   none of that pressure exists here.
2. **The object bill is trivial.** Per day: one 4H candle range box, four key-level lines (open, high,
   low, close of the anchor candle), the daily four (or just PDH/PDL which v1 already fetches), one
   week-open line, and one sweep marker. About ten objects a day, versus the 500-per-script ceiling
   that made the MX features a build constraint.
3. **No new `request.security` pressure for the core.** The anchor candle is chart data. Only the
   daily four-price ladder and SMT add calls, and v1 already spends three; one more tuple for
   `[o,h,l,c]` of `"D"` is the honest cost.

## 5. What I recommend not building, and why

* **Weekly market profile.** Pine has no TPO or volume-profile object. You can approximate a value
  area by bucketing the week's range by bar count, but it is a different measurement wearing the same
  name, and it would be the one thing in the panel that teaches you something false. If profile levels
  matter to you, that is a TradingView built-in (Volume Profile indicator), not our script.
* **A "+3RR" auto-target without an outcome record.** Fixed multiple targets are fine — `rr_target`
  already exists — but the only reason to trust one is a journal behind it. The archived v2 has the
  whole journal/funnel machinery (win rate, expectancy, Wilson lower bound, per-session buckets); if
  we ship this model, lifting that tracker is what turns it from a decoration into a test.
* **Anything called "Model 1".** Neither post defines it. I can reconstruct what the charts show, but
  naming our reconstruction after their brand would put a claim in the code that nothing supports.
  Either you send me the place where Model 1 is defined, or we name the rules we can see.

## 6. The build, as I would spec it (every line optional, defaults preserve today's behaviour)

```
grp_crt = "======= 4H candle range (optional) ======="
crtOn        = input.bool(false, "Use a 4H anchor candle as the day's reference")
crtAnchorHour= input.int(1, "Anchor 4H candle opens at this NY hour", 0..23)   // 1 = their 01:00
crtLevels    = input.bool(true, "Mark the anchor candle's open / high / low / close")
crtRangeBox  = input.bool(true, "Draw the anchor candle's range")
crtWinMin    = input.int(45, "Sweep must occur within N minutes of the anchor open")
crtMicro     = input.bool(false, "Micro CRT: require the same test on one 15m candle")
crtTs        = input.bool(true, "Require a Turtle Soup close-back-inside (not just a touch)")
crtBias      = input.string("HTF bias", "Direction filter", options=["None","HTF bias","Above/below TDO","HTF bias + TDO"])
crtEntry     = input.string("Anchor open", "Entry level", options=["Anchor open","Anchor open retest","15m OB","iFVG tap"])
crtTarget    = input.string("Opposite bound", "Target", options=["Opposite bound","Fixed R","Fixed R then opposite bound"])
crtReset     = input.bool(true, "One setup per anchor candle")
```
The arithmetic, with corpus citations attached in comments:
`anchor = the 4H bar whose open time == crtAnchorHour NY`, captured on its **close** (never the
forming candle — the range is not defined while it prints); `key_open = anchor.open`; `sweep_hi =
high > anchor.high and close < anchor.high` within `crtWinMin` (this is `liquidity-sweep.md`'s wick +
close-back-inside, and `turtle-soup.md`'s failure condition in one test); direction from `crtBias`
(00:00 NY `true-day-open` premium/discount, per `22-quarterly-theory/true-day-open.md`, combined with
the existing `htf_bull/htf_bear`); entry per `crtEntry`, reusing the OB registry and — if
`crtEntry = iFVG tap` — the inverted-zone machinery added in the last round, which is the same
"tap and reject a level" grammar with a different level; target `anchor.low`/`anchor.high` for the
corpus CRT, or `rr_target` for the "+3RR" convention, and I would show both because they disagree on
these very images.

Then the honest bit, which is what the v2 work was for: a counter of setups, of sweeps-that-became-
entries, and of which target was hit, so "Model 1" stops being a story.

## 7. Open questions before I build

1. Do you have a losing example from either account? The model's failure mode is what the panel should
   name — right now the only two examples both worked, so I am coding to a survivor.
2. `FR1` and the exact `Model 1` definition: a link to wherever they state it, or we invent our own
   names for what the charts actually show.
3. Is the target the opposite bound (community CRT) or +3R (these posts)? They are different trades and
   the images contradict themselves about which was taken.
4. Do you have the sibling-symbol data for SMT on your plan (it is in the archived overlay, ready to
   lift, and it is the one element here that needs an entitlement)?
