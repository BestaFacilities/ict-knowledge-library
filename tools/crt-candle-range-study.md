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

All four were answered from sources on the second pass - see §8. Only Q4 stays open, because it
needs your data entitlement. §11 supersedes this §6 spec, which had one structural error.

## 8. Answers, found in the sources rather than asked for (2026-10-10, second pass)

You said to look them up myself. I could reach the X pages through the fetch tool, so the three
accounts the screenshots credit are now read, and two of the four open questions answered themselves.

**Who is who.** `@SpeculatorFL` ("Sham", 40k followers, "Trader & teacher") is the source the other two
credit: his 2026-10-01 post is the model as a three-gate stop-list —

> 1. Have you determined daily bias? — Yes = step 2 / **No = stop**
> 2. Have you identified a key level and candle range? — Yes = step 3 / **No = stop**
> 3. Do you see your entry confirmation? — Yes = execute / **No = abandon**

and his trade posts give the levels: "4H Key level + Candle range. 15M Orderblock entry. **3am entry.**
Classic daily OHLC" and "Daily bias alignment. 4H Key level + **SMT**. 15M Orderblock. OHLC. My bread
and butter." `@EU_SNIPER_01` (748 followers, bio: "Candle Range Trader") is a student reposting that
checklist with his own labels; his 2026-10-05 post is "**Validate a Dealing Range using CISD**" — i.e.
the state-of-delivery change, which this script already computes, *is* his dealing-range validation.
`@ONESTrades` (2.8k) publishes the six-step version (Daily Bias → draw on liquidity → key levels →
4H CRT dealing range → LTF confirmation → execution with predefined risk) and adds "having a bias
doesn't mean we must take a trade… we stay risk-off". `@MadoCRT` (24k, "PhD in Candle Ranges") is the
one who supplies the governing rule: "**Time Condition > Price Condition.** If the price condition is
there but the time condition doesn't align, do absolutely nothing."

**Q2 (`Model 1`, `FR1`) — answered, and the answer is "don't name it".** MadoCRT is selling a program
called C³ starting 2026-10-15 and describes it as "integrated concepts from ICT, Wyckoff, Dow Theory,
Supply & Demand, traditional Market Structure… into one complete CRT framework. Its own logic. Its own
rules." So "Model 1" is course material behind a launch date, not a public definition; and neither
post states it. What the charts actually show is a raid of one bound of a reference candle, acceptance
back inside, an LTF OB or key-level tap, and delivery to the opposite bound — so the build names those
rules and refuses the brand name. `FR1`/`FRI` is not in any of their checklists at all; on the widest
of the two close-ups it reads as the weekday marker next to `W OPEN`, which is the only reading the
evidence supports, so it is treated as **not load-bearing** and left out of the model.

**Q3 (target) — answered, and it also dissolves the +3RR contradiction.** Community CRT targets the
opposite extreme of the reference candle; the worked example on crttrading.com runs **50% of the range
(partial, stop to breakeven), then the opposite bound**. That ladder produces realised rewards of ~1.6R
to ~2.8R — which is what the EU panel's box actually measures (2.2R). So "+3RR" is a *ceiling label*,
not the target that was taken. Default is the opposite bound; "50% then opposite bound" and "R multiple"
are options; the panel prints the R available at the bound so the convention is testable rather than
copyable.

**Q1 (the failures) — answered from sources, and it turned out to be the most useful find.** Not from
the accounts (they publish winners only — both breakdowns are boxes drawn after the fact) but from the
library: `15-sessions/london-session-avoidance.md` is ICT's own stand-aside list for the April-2017
London model, which is the same session and year this variant is anchored to (§2), and
`25-htf-bias/weekly-range-profiles.md` names the day-shape that kills a candle-range day ("seek and
destroy Friday… a neutral or low probability market profile… better to avoid trading these conditions
altogether"). That is why the failures are implemented as gates rather than documented as cautions —
see §10.

**Q4 (SMT) — still yours.** It is the one element that needs sibling-symbol data on your plan. Not
built; the archived overlay has a working module to lift the moment you say you have it.

## 9. Sources consulted, with what each contributed

X (read through the fetch tool on 2026-10-10; these are promotional accounts, so they are a
**specification** source and are cited as such, never as evidence):

| post | date | what it settled |
|---|---|---|
| x.com/SpeculatorFL/status/2105550387126383099 | 2026-10-01 | the three-gate stop/abandon checklist; top reply "somehow the no always gets negotiated into a yes when you're bored" |
| x.com/SpeculatorFL/status/2108542004447809945 | 2026-10-09 | "4H Key level + Candle range. 15M Orderblock entry. 3am entry. Classic daily OHLC" — the entry hour is a *choice*, not 01:30 |
| x.com/SpeculatorFL/status/2105549494796648894 | 2026-10-01 | SMT inside the core checklist, not as an extra |
| x.com/EU_SNIPER_01/status/2107136781934379034 | 2026-10-05 | "Validate a Dealing Range using CISD" — the CISD link, asked about in a reply ("which TF CISD confirms an H4 dealing range?") |
| x.com/EU_SNIPER_01/status/2106242396833067034 | 2026-10-03 | the full checklist with "Thanks @SpeculatorFL" — provenance of the model |
| x.com/MadoCRT/status/2108091131028537371 | 2026-10-08 | "Time Condition > Price Condition" — the time window as a hard gate |
| x.com/MadoCRT/status/2108490484104737167 | 2026-10-09 | C³ launch framing: a closed system, "its own rules", sold not published |
| x.com/ONESTrades/status/2108912056292553139 | 2026-10-10 | the six-step framework; "bias doesn't mean we must take a trade… we stay risk-off" |
| x.com/ONESTrades/status/2108488887614288084 | 2026-10-09 | their own stated risk: "still experiencing a range-bound week… let's see if we get the expected move or if price continues to range" |

Secondary (public explainer/industry pages; note their numbers are self-reported and none is audited):

* **luxalgo.com/library/concept/candle-range-theory** — the cleanest mechanical statement found: mark
  candle 1's high/low *and 50%*, candle 2 must **close back inside**, "a close beyond the extreme… the
  CRT is void in that direction", a **delivery window of candle 3**, the built-in target is the
  opposite extreme, most weight when the raid lands **on a HTF key level**, "a CRT in open space" is
  weak, and the honest caveat: "**No independent, published study tests it**, and most claims about it
  online are anecdotal… Backtesting the exact rules you trade… is the only way to know".
* **crttrading.com** §09/§10/§13/§14 — filter ladder ~45% raw → ~60% with HTF bias → ~70% with
  killzone + structure shift; "Trading CRTs against the higher-timeframe trend is the largest win-rate
  killer"; setups outside the killzones "frequently fail because there's not enough institutional flow
  to drive price to the opposite extreme"; the 50%-then-bound worked example; and its own reality check
  that these rates are "not audited".
* **tradingwyckoff.com/en/crt** — same shape of table (45-50% raw → 60-65% filtered), "a bullish CRT
  inside a daily bearish trend has <40% win rate", "M1 CRTs in Asia session have near-zero edge",
  "works on daily and 4H — not on M1/M5 due to noise", stop "below the sweep low… no closer, no
  farther", max 2-3 trades/day, lineage (Wyckoff spring/upthrust → Raschke turtle soup → ICT sweep/AMD
  → community CRT 2024).
* **arongroups.co** — the failure taxonomy: "CRT's biggest failure case is a **false range** (poorly
  chosen HTF candle) or **shifting boundaries** (you keep redefining the range to fit price)";
  "no re-entry = no trade"; "starts to accept back inside (not just a one-tick touch)".
* **fundingpips.com/blog/ict-silver-bullet-strategy-explained** — independent backtests of a sibling
  time-boxed ICT model land at **50-65%**, not the 70-80% in the marketing; and "treat the time
  restriction as its core discipline mechanism, not an inconvenience to work around".
* **crtterminal.com** — a product that runs this definition as a "deterministic detection engine"
  logging "every parent, sweep, confirmation, and order block… and why a trading setup fired — or why
  it didn't". Right architecture, and the reason the non-firing path is a first-class feature here.

Corpus pages that did the real work on failures: `15-sessions/london-session-avoidance.md`
(ICT-2017-AVOID-LONDON), `25-htf-bias/weekly-range-profiles.md` (ICT-2017-STT-WEEKLY-PROFILES),
`21-crt/crt-rules.md`, `20-turtle-soup/turtle-soup.md`, `02-liquidity/liquidity-sweep.md`,
`10-killzones/killzone-times-table.md`, `22-quarterly-theory/true-week-open.md`.

## 10. The failures, as a list the code can enforce

Eight named failure modes, each with the source that names it and the switch that handles it. This is
the answer to "code to a survivor": the panel now reports the days it refused as loudly as the setups
it found.

| # | failure | source | in `grp_crt` |
|---|---|---|---|
| F1 | **no raid at all** — a range day: the bound is never taken | their own "No = stop" | state stays `watching`; `crtSeen` counts the day, `crtSweeps` does not |
| F2 | **raid then acceptance** — price closes beyond the bound, so the break held | "the CRT is void in that direction" (luxalgo) | `crtState → void`, note "accepted outside the range" |
| F3 | **out of time** — the price condition is there, the time condition is not | MadoCRT; "outside the killzones… frequently fail" | `crtTimeHard` + `crtWinOpen`/`crtWinLen`; `void: no raid before the delivery window closed` |
| F4 | **one-tick re-entry** — a touch, not acceptance | arongroups | `crtAccept` (touch / close / close + body) |
| F5 | **counter-bias** — the largest win-rate killer | crttrading §09, wyckoff (<40%) | `crtBias`, counted separately as `crtFiltered` so you can see what the filter costs |
| F6 | **both bounds taken** — a two-way day | "seek and destroy Friday… neutral or low probability" | `void: both bounds raided - a seek-and-destroy day` |
| F7 | **the day was never tradeable** — large prior range, blown-out overnight, no build-up, NFP Friday | ICT-2017-AVOID-LONDON (A1/A3/B1/B2/B3/B4/C) | `crtSA` + the five thresholds; the panel names **which** condition, and `crtSkips` counts the days |
| F8 | **no delivery** — armed or even in the trade, but the target never prints | "candle 3" delivery window (luxalgo) | `crtDeliverH` → counted as void, not left open until it happens to work |
| F9 | **a box that is a spread** | this repo's own −0.216R-after-friction result (audit §13) | `crtMinRiskT`, plus the refusal when risk exceeds 1.5× the reference range |

Three of ICT's eight stand-aside conditions are calendar facts — a specific holiday, an unscheduled
driver, and the count of scheduled high-impact events. Pine cannot see a calendar, so they are left
out rather than approximated from a date field, and the input that stands in for the NFP case
(first Friday of the month) defaults to **Mark only**: the panel says it, you decide.

## 11. What shipped (supersedes §6, which was wrong in one place)

§6's spec said: take the 01:00 candle as the reference and watch for a raid *inside* it. That is
impossible — at 01:30 the 01:00 candle's bounds are not finished, so there is nothing to raid yet. The
only coherent reading of "4h 1 AM CRT" + "Key Timing 01:30 liquidity sweep" is the classic one: the
reference is the **4H candle ending at 01:00 NY** (candle 1, its range and open), and the **01:00 candle
is candle 2**, whose first hour is where the raid must happen. The build implements that, keeps
`Intra-anchor (provisional bounds)` as an explicit opt-in *named for the failure it causes*, and adds a
daily-reference mode for the daily CRT variant.

Shipped as the `grp_crt` block of `tools/cisd-ultimate-balanced.pine` — 26 inputs, every one of them
default-off or default-neutral, so the file behaves exactly as before until `crtOn` is switched on
(§6's input list is superseded by the real block, which also adds `crtTimeHard`, `crtDraw`, `crtObAge`,
`crtStop`, `crtMinRiskT`, `crtTrendFrac`, `crtTightFrac`, `crtGateCore`, `scCrt`):

* the reference candle is accumulated from chart bars by NY clock, not from `request.security(syminfo.tickerid,"240")`, so a 17:00-anchored template and a 00:00-anchored one agree about which candle is which;
* the daily ladder (prior-day OHLC + the 5-day ADR + the three-consecutive-close tests) was folded into the **existing** `"D"` call as an 8-value tuple, so the layer costs **zero** additional `request.security` calls;
* nine objects, created once and moved, never per day (this is what makes it fit alongside the 500 ceiling);
* the two new panel rows read `4H CRT` (state + the three levels) and `CRT why` (the last thing that happened, the running W/L/be/void count, the average R available at the bound, and how many days were refused and for what);
* four `alertcondition`s (raid, entry, outcome, void) so the failure path is alertable too;
* `crtGateCore`/`scCrt` are the only hooks into the CISD core, both off: on, the candle-range state vetoes or scores the `BEST` signal.

Three switches were added on the same day, after checking the build against the C1/C2/C3 sequence the
literature describes rather than against my own notes: `Reference candle length (min)` (240 = the 4H
anchor in the screenshots, 60 = the hourly anchors `21-crt/crt-rules.md` lists, which the first build
could not express because the span was hardcoded in three places), `Acceptance is C2's own close`
(the textbook C2 test, off by default because the screenshots enter mid-C2), and `Enter only inside C3`
(the delivery candle as an entry gate). It also surfaced a real bug: in provisional mode the raid was
tested against a bound that already contained the bar being tested, so it could never fire — fixed by
judging the raid and the acceptance against the level that existed before the bar, while the target
stays the candle's opposite bound. What is still *not* wired in: a structure-shift requirement inside
C3, because `cisd` is defined after this block in the file and Pine forbids the forward reference; the
entry block would have to move below the CISD core for that.

Verification was the whole gate order, plus three new **exercise variants** in `tools/pine-gate-run.py`.
The first forced-on run reported `crtSeen=0`: pyne executes 1-day synthetic bars whose clock never
moves, so a time-anchored layer sits inert no matter what the switch says — a clean exit that proved
nothing, which is the trap this harness exists for. The harness now refuses to pass an exercise whose
counters stay at zero, and the two variants (daily reference; intra-anchor accumulator, entry fired,
stop taken, net −1R) are the positive controls.
