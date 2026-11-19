#!/usr/bin/env python3
"""AST regression for SNM+ 3.62's NY PM active-liquidity and display changes.

Run with hoox-pyne installed: python tools/tests/test_snm_level_rendering.py
The active sweep/target helpers must remain identical to 3.61. Swept history is display-only,
while the configurable NY PM high/low is deliberately registered as active liquidity and uses
that existing sweep path. Positive controls mutate the sweep predicate, NY PM registration and
core classification, priority selection, history eviction/cap and sweep endpoint; the AST must detect them.
This is not TradingView compilation or chart-rendering verification.
"""
from pathlib import Path
import subprocess

from pynescript.ast import If, dump, parse, unparse, walk

BASE = "cb10a7e"
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
    assert len(nodes) == 1, (header, len(nodes))
    return nodes[0]


def sweep_projection(tree, header=SWEEP_HEADER):
    node = find_if(tree, header)
    return [dump(node.test)] + [dump(stmt) for stmt in node.body if head(stmt) != "f_lvHitAdd(v)"]


def main():
    old_source = subprocess.check_output(["git", "show", BASE + ":tools/snm-plus.pine"], cwd=ROOT, text=True)
    new_source = CURRENT.read_text()
    old = parse(old_source)
    new = parse(new_source)

    # No active-liquidity, target, continuation, or setup engine helper changed.
    for name in ("f_sweep", "f_draw", "f_edge", "f_addLv", "f_addSw", "f_preview"):
        assert dump(function(old, name)) == dump(function(new, name)), f"non-display helper changed: {name}"
    old_sweep = find_if(old, SWEEP_HEADER)
    new_sweep = find_if(new, SWEEP_HEADER)
    assert [head(stmt) for stmt in old_sweep.body] == ["f_sweep(v)", "f_lvHitAdd(v)", "lvs.remove(i)"]
    assert [head(stmt) for stmt in new_sweep.body] == ["f_sweep(v)", "f_lvHitAdd(v)", "lvs.remove(i)"]
    assert sweep_projection(old) == sweep_projection(new), "sweep handling changed beyond the history-record call"

    # NY PM (default 13:00–16:00 New York) joins the common active-session level path.
    assert 'bool iNypm = input.bool(true, "NY PM"' in new_source
    assert 'string sNypm = input.session("1300-1600"' in new_source
    assert "bool inNypm = f_in(sNypm)" in new_source
    assert 'array<string> sNm = array.from("ASIA", "LON", "PRE", "AM", "NYPM")' in new_source
    assert 'var array<float> sH = array.new<float>(5, na)' in new_source
    assert 'var array<bool> sWas = array.new<bool>(5, false)' in new_source
    session_gate = find_if(new, "if barstate.isconfirmed and calc")
    session_text = unparse(session_gate)
    assert "iNypm and inNypm" in session_text
    assert "for s = 0 to 4" in session_text
    assert 'f_addLv(sH.get(s), true, sNm.get(s) + ".H"' in session_text
    assert 'f_addLv(sL.get(s), false, sNm.get(s) + ".L"' in session_text
    assert 'sNm.get(s) + ".H"' in session_text and 'sNm.get(s) + ".L"' in session_text

    # Active session + prior-day levels bypass the optional additional-level count by default.
    assert 'bool iLvCore = input.bool(true, "Always show sessions + PDH/PDL"' in new_source
    assert 'int iLvN = input.int(2, "other / side", minval = 0' in new_source
    core = unparse(function(new, "f_isCoreLevel"))
    for name in ('"PDH"', '"PDL"', '"ASIA."', '"LON."', '"PRE."', '"AM."', '"NYPM."'):
        assert name in core, name
    levels = find_if(new, LEVEL_HEADER)
    level_text = unparse(levels)
    assert "bool coreDone = not iLvCore" in level_text
    assert "bool corePass = iLvCore and not coreDone" in level_text
    assert "bool wanted = corePass ? core : not iLvCore or not core" in level_text
    assert "int otherLimit = cleanView ? 1 : iLvN" in level_text

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

    # Positive control 1: removing NY PM from the session selector must trip the level-engine AST.
    session_selector = "iNypm and inNypm"
    assert new_source.count(session_selector) == 1
    bad_session = parse(new_source.replace(session_selector, "false", 1))
    assert dump(find_if(bad_session, "if barstate.isconfirmed and calc")) != dump(session_gate), "positive control missed NY PM session registration"

    # Positive control 2: omitting NYPM from core classification must trip that helper's AST.
    core_marker = 'str.startswith(nm, "NYPM.")'
    assert new_source.count(core_marker) == 1
    bad_core = parse(new_source.replace(core_marker, 'str.startswith(nm, "NYPMX.")', 1))
    assert dump(function(bad_core, "f_isCoreLevel")) != dump(function(new, "f_isCoreLevel")), "positive control missed NY PM core priority"

    # Positive control 3: a sweep boundary mutation must trip the AST projection.
    assert old_source.count(SWEEP_HEADER) == 1
    mutated_header = "if v.hi ? high >= v.px : low < v.px"
    bad_sweep = parse(old_source.replace(SWEEP_HEADER, mutated_header, 1))
    assert sweep_projection(bad_sweep, mutated_header) != sweep_projection(new), "positive control missed changed sweep predicate"

    # Positive control 4: reversing the core/secondary selector must trip the rendered block AST.
    selector = "bool wanted = corePass ? core : (not iLvCore or not core)"
    assert new_source.count(selector) == 1
    bad_priority = parse(new_source.replace(selector, "bool wanted = corePass ? not core : (not iLvCore or not core)", 1))
    assert dump(find_if(bad_priority, LEVEL_HEADER)) != dump(levels), "positive control missed changed priority"

    # Positive control 5: evicting core history first must trip the helper AST.
    eviction = "if not lvHits.get(i).core"
    assert new_source.count(eviction) == 1
    bad_eviction = parse(new_source.replace(eviction, "if lvHits.get(i).core", 1))
    assert dump(function(bad_eviction, "f_lvHitAdd")) != dump(hit_add), "positive control missed changed core-history priority"

    # Positive control 6: an off-by-one history cap must trip the helper AST.
    cap = "while lvHits.size() > iLvHist"
    assert new_source.count(cap) == 1
    bad_cap = parse(new_source.replace(cap, "while lvHits.size() >= iLvHist", 1))
    assert dump(function(bad_cap, "f_lvHitAdd")) != dump(hit_add), "positive control missed changed history cap"

    # Positive control 7: extending a new segment one bar past its sweep must be visible in the helper AST.
    endpoint = "line.new(x1, v.px, bar_index, v.px"
    assert new_source.count(endpoint) == 1
    bad_endpoint = parse(new_source.replace(endpoint, "line.new(x1, v.px, bar_index + 1, v.px", 1))
    assert dump(function(bad_endpoint, "f_lvHitAdd")) != dump(hit_add), "positive control missed changed sweep endpoint"

    print("PASS: 3.61 sweep/target helpers unchanged; NY PM joins active liquidity; swept history is display-only; seven AST mutation controls fired")


if __name__ == "__main__":
    main()
