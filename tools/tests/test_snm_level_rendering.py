#!/usr/bin/env python3
"""AST regression for SNM+ 3.63 levels and 3.64's compact MX Lite view.

Run with hoox-pyne installed: python tools/tests/test_snm_level_rendering.py
The active sweep/target path must remain identical to 3.62. Completed Asia, London and NY
ranges use DD/MM labels; the date is taken from the New York calendar date of each extreme bar.
A separate NY AM rulebook window remains for the original reversal / Sweep + CISD gate.
Positive controls mutate session registration, the combined NY hours, date formatting, stable
session identity, core priority, sweep handling and swept-history behavior. This is not TradingView
compilation or chart-rendering verification.
"""
from pathlib import Path
import subprocess

from pynescript.ast import If, dump, parse, unparse, walk

BASE = "8208b5c"
ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "tools/snm-plus.pine"
SWEEP_HEADER = "if v.hi ? high > v.px : low < v.px"
LEVEL_HEADER = "if iLvShow and lvs.size() > 0"


def function(tree, name):
    nodes = [node for node in tree.body if getattr(node, "name", None) == name]
    assert len(nodes) == 1, (name, len(nodes))
    return nodes[0]


def head(node):
    return unparse(node).split("\n", 1)[0]


def find_if(tree, header):
    nodes = [node for node in walk(tree) if isinstance(node, If) and head(node) == header]
    assert len(nodes) >= 1, (header, len(nodes))
    # CW10003 fix splits the engine into two `if barstate.isconfirmed and calc` blocks
    # (main engine, then new chart gaps after the unconditional f_setup calls).
    # The first block holds session registration; callers that need it use nodes[0].
    return nodes[0]


def sweep_projection(tree, header=SWEEP_HEADER):
    node = find_if(tree, header)
    return [dump(node.test)] + [dump(stmt) for stmt in node.body if head(stmt) != "f_lvHitAdd(v)"]


def replace_once(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new, 1)


def main():
    old_source = subprocess.check_output(["git", "show", BASE + ":tools/snm-plus.pine"], cwd=ROOT, text=True)
    new_source = CURRENT.read_text()
    old = parse(old_source)
    new = parse(new_source)

    # No sweep, target, edge, swing or swept-history logic changed. f_preview is
    # excluded: 3.68 removed the TTrades (TTFM) tooltip text from it. f_sweep,
    # f_draw and f_edge are excluded: 3.69 removed Judas (s.jx), NWOG draws and
    # 5M HTF gap zones from them. f_addSw and f_lvHitAdd remain byte-identical.
    for name in ("f_addSw", "f_lvHitAdd"):
        assert dump(function(old, name)) == dump(function(new, name)), f"active/display helper changed: {name}"
    # 3.69 extras are gone from the sweep/target path.
    for gone in ("iNwog", "iMon", "MON.H", "iJudas", "inJudas", "s.jx", "f_zAdd5", "f_zSponsor", "iZ5"):
        assert gone not in new_source, f"removed extra still present: {gone}"
    old_sweep = find_if(old, SWEEP_HEADER)
    new_sweep = find_if(new, SWEEP_HEADER)
    assert [head(stmt) for stmt in old_sweep.body] == ["f_sweep(v)", "f_lvHitAdd(v)", "lvs.remove(i)"]
    assert [head(stmt) for stmt in new_sweep.body] == ["f_sweep(v)", "f_lvHitAdd(v)", "lvs.remove(i)"]
    assert sweep_projection(old) == sweep_projection(new), "sweep handling changed beyond the history-record call"

    # The only active-registry helper change is stable identity for date-prefixed session names.
    old_add = unparse(function(old, "f_addLv"))
    identity_comparison = "if lvs.get(i).nm == nm"
    assert old_add.count(identity_comparison) == 2
    expected_add = old_add.replace(identity_comparison, "if f_lvKey(lvs.get(i).nm) == f_lvKey(nm)", 1)
    new_add = unparse(function(new, "f_addLv"))
    assert expected_add == new_add, "active-level insertion changed beyond dated session identity"

    # Exactly one combined NY liquidity range; NY AM stays only as a separate rulebook clock.
    assert 'bool iNy = input.bool(true, "New York (NY)"' in new_source
    assert 'string sNy = input.session("0930-1600"' in new_source
    assert "bool inNy = f_in(sNy)" in new_source
    assert 'string sNyRule = input.session("0930-1100", "NY AM rulebook window"' in new_source
    assert "bool inAm = f_in(sNyRule)" in new_source
    assert 'bool iSessDate = input.bool(true, "Date-stamp Asia/London/NY labels"' in new_source
    assert 'array<bool> inS = array.from(iAs and inAs, iLo and inLo, iPr and inPr, iNy and inNy)' in new_source
    assert 'array<string> sNm = array.from("ASIA", "LON", "PRE", "NY")' in new_source
    assert 'for s = 0 to 3' in new_source
    assert "iAm" not in new_source and "iNypm" not in new_source and "sNypm" not in new_source and "NYPM" not in new_source
    assert new_source.count("not inAm") == 3, "the original NY AM rulebook checks must remain separate from the NY pool"
    assert "inAm ? f_left(sNyRule)" in new_source
    assert 'string iWin = input.string("2000-0000,0200-0500,0930-1100"' in new_source

    # Track the timestamp of each extreme bar so its visible date is stable and timezone-explicit.
    for declaration in (
        'var array<int> sHt = array.new<int>(4, 0)',
        'var array<int> sLt = array.new<int>(4, 0)',
        'sHt.set(s, time)',
        'sLt.set(s, time)',
        'f_sessionLevelName(sNm.get(s), true, sHt.get(s))',
        'f_sessionLevelName(sNm.get(s), false, sLt.get(s))',
    ):
        assert declaration in new_source, declaration
    assert new_source.count("sHt.set(s, time)") == 2
    assert new_source.count("sLt.set(s, time)") == 2
    label_fn = unparse(function(new, "f_sessionLevelName"))
    assert 'str.format_time(levelTime, "dd/MM", NY)' in label_fn
    assert 'sessionName == "PRE" or not iSessDate ? base :' in label_fn, "premarket stays undated and the date prefix can be toggled off"
    key_fn = unparse(function(new, "f_lvKey"))
    assert 'str.substring(nm, 2, 3) == "/"' in key_fn
    assert 'str.substring(nm, 5, 6) == " "' in key_fn
    assert 'str.substring(nm, 6, str.length(nm))' in key_fn
    dated_session_fn = unparse(function(new, "f_isDatedSessionLevel"))
    for name in ('"ASIA.H"', '"ASIA.L"', '"LON.H"', '"LON.L"', '"NY.H"', '"NY.L"'):
        assert name in dated_session_fn, name
    session_fn = unparse(function(new, "f_isSessionLevel"))
    for name in ('"ASIA.H"', '"ASIA.L"', '"LON.H"', '"LON.L"', '"PRE.H"', '"PRE.L"', '"NY.H"', '"NY.L"'):
        assert name in session_fn, name
    assert "f_isSessionLevel(nm)" in unparse(function(new, "f_isCoreLevel"))
    assert 'string tx = v.nm + (v.hrl ? " · HRL" : f_isDatedSessionLevel(v.nm) ? "" : " $$$")' in new_source

    # Core session + prior-day levels stay additive to the selected per-side secondary count.
    assert 'bool iLvCore = input.bool(true, "Always show sessions + PDH/PDL"' in new_source
    assert 'int iLvN = input.int(2, "", minval = 0' in new_source  # CW10026: inline inputs after the first carry no title
    levels = find_if(new, LEVEL_HEADER)
    level_text = unparse(levels)
    assert "bool coreDone = not iLvCore" in level_text
    assert "bool corePass = iLvCore and not coreDone" in level_text
    assert "bool wanted = corePass ? core : not iLvCore or not core" in level_text
    assert "int otherLimit = iLvN" in level_text  # 3.68: views removed, always Current density

    # Taken levels are capped display records and their line terminates at the sweep bar.
    assert 'bool iLvSwept = input.bool(true, "Keep swept levels to their sweep"' in new_source
    hit_add = function(new, "f_lvHitAdd")
    hit_text = unparse(hit_add)
    assert "if iLvSwept and iLvShow" in hit_text
    assert "old.sweepB == bar_index" in hit_text
    assert "while lvHits.size() > iLvHist" in hit_text
    assert "old.core := old.core or f_isCoreLevel(v.nm)" in hit_text
    assert "if not lvHits.get(i).core" in hit_text
    assert "line.new(x1, v.px, bar_index, v.px" in hit_text
    assert "line.set_xy2(old.ln, old.sweepB, old.px)" in hit_text
    assert "label.set_xy(old.lb, old.sweepB, old.px)" in hit_text
    assert "line.delete(dropped.ln)" in hit_text and "label.delete(dropped.lb)" in hit_text

    # Positive control 1: removing the combined NY range from the selector trips registration.
    session_gate = find_if(new, "if barstate.isconfirmed and calc")
    session_selector = "iNy and inNy"
    bad_session = parse(replace_once(new_source, session_selector, "false"))
    assert dump(find_if(bad_session, "if barstate.isconfirmed and calc")) != dump(session_gate), "positive control missed NY registration"

    # Positive control 2: shifting the session back to an AM-only range is detected.
    bad_hours_source = replace_once(new_source, 'input.session("0930-1600"', 'input.session("0930-1100"')
    bad_hours = parse(bad_hours_source)
    assert unparse(bad_hours) != unparse(new), "positive control missed the combined NY hours"

    # Positive control 3: changing the required DD/MM label format trips the date-name helper.
    bad_date = parse(replace_once(new_source, 'str.format_time(levelTime, "dd/MM", NY)', 'str.format_time(levelTime, "MM/dd", NY)'))
    assert unparse(function(bad_date, "f_sessionLevelName")) != label_fn, "positive control missed changed date format"

    # Positive control 4: restoring full-label equality would accumulate a new live level each day.
    bad_identity = parse(replace_once(new_source, "if f_lvKey(lvs.get(i).nm) == f_lvKey(nm)", identity_comparison))
    assert unparse(function(bad_identity, "f_addLv")) != new_add, "positive control missed unstable dated identity"

    # Positive control 5: omitting NY levels from core classification must trip the helper AST.
    core_marker = 'key == "NY.H" or key == "NY.L"\n\nf_isCoreLevel'
    bad_core = parse(replace_once(new_source, core_marker, 'key == "NY.X" or key == "NY.L"\n\nf_isCoreLevel'))
    assert unparse(function(bad_core, "f_isSessionLevel")) != session_fn, "positive control missed NY core priority"

    # Positive control 6: a sweep boundary mutation must trip the AST projection.
    mutated_header = "if v.hi ? high >= v.px : low < v.px"
    bad_sweep = parse(replace_once(old_source, SWEEP_HEADER, mutated_header))
    assert sweep_projection(bad_sweep, mutated_header) != sweep_projection(new), "positive control missed changed sweep predicate"

    # Positive control 7: reversing the core/secondary selector must trip the rendered block AST.
    selector = "bool wanted = corePass ? core : (not iLvCore or not core)"
    assert new_source.count(selector) == 1
    bad_priority = parse(replace_once(new_source, selector, "bool wanted = corePass ? not core : (not iLvCore or not core)"))
    assert dump(find_if(bad_priority, LEVEL_HEADER)) != dump(levels), "positive control missed changed priority"

    # Positive control 8: evicting core history first must trip the helper AST.
    eviction = "if not lvHits.get(i).core"
    bad_eviction = parse(replace_once(new_source, eviction, "if lvHits.get(i).core"))
    assert dump(function(bad_eviction, "f_lvHitAdd")) != dump(hit_add), "positive control missed changed core-history priority"

    # Positive control 9: an off-by-one history cap must trip the helper AST.
    cap = "while lvHits.size() > iLvHist"
    bad_cap = parse(replace_once(new_source, cap, "while lvHits.size() >= iLvHist"))
    assert dump(function(bad_cap, "f_lvHitAdd")) != dump(hit_add), "positive control missed changed history cap"

    # Positive control 10: extending a new segment one bar past its sweep must trip the helper AST.
    endpoint = "line.new(x1, v.px, bar_index, v.px"
    bad_endpoint = parse(replace_once(new_source, endpoint, "line.new(x1, v.px, bar_index + 1, v.px"))
    assert dump(function(bad_endpoint, "f_lvHitAdd")) != dump(hit_add), "positive control missed changed sweep endpoint"

    print("PASS: 3.62 sweep/target paths preserved; combined NY + dated session labels registered; swept history/core priority and compact-view level count intact; ten AST mutation controls fired")


if __name__ == "__main__":
    main()
