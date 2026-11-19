#!/usr/bin/env python3
"""AST regression for the SNM+ 3.64 MX Lite display-only controls.

Run with hoox-pyne installed: python tools/tests/test_snm_mx_lite.py
The test compares the active 3.63 source with 3.64. MX Lite is opt-in; the
independent visibility controls are default-On and non-destructive. The test
checks the drawing mute, retained tracker objects, and reuse of the prior Clean
layout conditions without changing setup logic. It cannot verify TradingView
rendering or object behavior in replay.
"""
from pathlib import Path
import subprocess

from pynescript.ast import dump, parse, unparse

BASE = "b5d2cb7"  # SNM+ 3.63 immediately before MX Lite
ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "tools/snm-plus.pine"


def function(tree, name):
    nodes = [node for node in tree.body if getattr(node, "name", None) == name]
    assert len(nodes) == 1, (name, len(nodes))
    return nodes[0]


def head(node):
    return unparse(node).split("\n", 1)[0]


def source_at(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True)


def setup_body(tree):
    body = function(tree, "f_setup").body
    # CW10003 fix: setup logic is wrapped in `if d != 0` for unconditional calls.
    if len(body) >= 1 and head(body[0]) == "if d != 0":
        return list(body[0].value.body) + list(body[1:])
    return body


def shown_setup(tree):
    nodes = [node for node in setup_body(tree) if head(node) == "if show"]
    assert len(nodes) == 1
    return nodes[0].value.body


def check_tracker_visibility(old_tree, new_tree):
    old_fn = function(old_tree, "f_trkEnd")
    new_fn = function(new_tree, "f_trkEnd")
    old_writes = [i for i, node in enumerate(old_fn.body) if head(node).startswith("t.lb.set_text(t.txt + ")]
    new_guards = [i for i, node in enumerate(new_fn.body) if head(node) == "if t.tagVisible"]
    assert len(old_writes) == 1 and len(new_guards) == 1, "tracker label writes must be guarded only for hidden tags"
    oi, ni = old_writes[0], new_guards[0]
    assert [dump(node) for node in old_fn.body[:oi]] == [dump(node) for node in new_fn.body[:ni]], "tracker outcome state or accounting changed"
    assert [dump(node) for node in new_fn.body[ni].value.body] == [dump(node) for node in old_fn.body[oi:oi + 2]], "visible tracker label result changed"
    assert [dump(node) for node in new_fn.body[ni + 1:]] == [dump(node) for node in old_fn.body[oi + 2:]], "tracker function return changed"


def main():
    old_source = source_at(BASE, "tools/snm-plus.pine")
    new_source = CURRENT.read_text()
    old = parse(old_source)
    new = parse(new_source)

    assert 'indicator("SNM+ 3.64", shorttitle = "SNM+ 3.64"' in new_source
    assert 'input.string("Current (3.54)", "Chart view", options = ["Current (3.54)", "Clean", "MX Lite"]' in new_source
    assert 'bool cleanView = iView == "Clean"' in new_source
    assert 'bool mxLiteView = iView == "MX Lite"' in new_source
    assert "bool compactView = cleanView or mxLiteView" in new_source
    assert 'input.bool(true, "Show setup labels"' in new_source
    assert 'input.bool(true, "Show setup zones / iFVGs"' in new_source
    assert 'input.bool(true, "Latest setup only (MX Lite)"' in new_source
    for name in ("f_sweep", "f_draw", "f_edge", "f_addSw", "f_preview", "f_lvHitAdd", "f_trk"):
        assert dump(function(old, name)) == dump(function(new, name)), f"model helper changed: {name}"

    # The grade/display gate and label payload inputs remain unchanged.
    old_setup = function(old, "f_setup")
    new_setup = function(new, "f_setup")
    for tree in (old, new):
        show_gate = [node for node in setup_body(tree) if head(node).startswith("bool show =")]
        assert len(show_gate) == 1
    assert dump(next(node for node in setup_body(old) if head(node).startswith("bool show ="))) == dump(
        next(node for node in setup_body(new) if head(node).startswith("bool show ="))
    ), "setup grade/window/dedup gate changed"
    assert dump(function(old, "f_preview")) == dump(function(new, "f_preview"))
    check_tracker_visibility(old, new)
    assert "bool tagVisible = true" in new_source

    old_children = shown_setup(old)
    new_children = shown_setup(new)
    old_box = unparse(next(node for node in old_children if head(node).startswith("st.bx := box.new")))
    new_box = unparse(next(node for node in new_children if head(node).startswith("st.bx := box.new")))
    # CE10117 fix: the box is always created (so f_stDel can delete it unconditionally);
    # iZoneShow Off makes it fully transparent instead of skipping creation.
    assert "g.t0" in new_box and "g.top" in new_box and "g.bot" in new_box
    assert "bgcolor=color.new(c, iZoneShow ? 85 : 100)" in new_box
    assert "border_color=color.new(c, 100)" in new_box

    old_zone = unparse(next(node for node in old_children if head(node).startswith("st.tl.push(label.new")))
    new_zone = unparse(next(node for node in new_children if head(node).startswith("st.tl.push(label.new")))
    assert 'iZoneShow ? (cd ? "CISD" : g.tf + " iFVG") : ""' in new_zone
    assert 'tooltip=iZoneShow ? gTip : ""' in new_zone
    assert "g.t0" in old_zone and "gMid" in old_zone and "g.t0" in new_zone and "gMid" in new_zone

    old_tag = unparse(next(node for node in old_children if head(node).startswith("st.lb := label.new")))
    new_tag = unparse(next(node for node in new_children if head(node).startswith("st.lb := label.new")))
    assert 'iSigShow ? lbTxt : ""' in new_tag
    assert 'tooltip=iSigShow ? tip : ""' in new_tag
    # Hidden tag: fully transparent background and text (100 = transparent in Pine).
    assert "not iSigShow or not pill ? 100" in new_tag
    assert "iSigShow ? 0 : 100" in new_tag
    assert "Tr.new(" in new_source and "st.lb" in new_source, "tracker must retain the setup label ID"
    assert "label.new" in old_tag and "label.new" in new_tag

    # Latest-only is a drawing mute pass before the ordinary record push/cap.
    recent = next(node for node in new_children if head(node) == "if mxLiteView and iMxRecent and sts.size() > 0")
    recent_text = unparse(recent)
    assert "for oldSt in sts" in recent_text and "f_stFade(oldSt, true)" in recent_text
    assert "for oldTr in trs" in recent_text and "oldTr.tagVisible := false" in recent_text
    assert "delete" not in recent_text and "sts.remove" not in recent_text and "sts.clear" not in recent_text
    assert "alert(" not in recent_text
    assert "nt.tagVisible := iSigShow" in new_source
    new_heads = [head(node) for node in new_children]
    assert new_heads.index("if mxLiteView and iMxRecent and sts.size() > 0") < new_heads.index("if iTrack and okWin")
    assert new_heads.index("if mxLiteView and iMxRecent and sts.size() > 0") < new_heads.index("sts.push(st)")
    # CE10117 fix merged f_stHide into f_stFade: hiding clears text and tooltips without deleting IDs.
    fade_fn = unparse(function(new, "f_stFade"))
    assert 'label.set_text(st.lb, "")' in fade_fn and 'label.set_tooltip(st.lb, "")' in fade_fn
    assert 'label.set_text(lab, "")' in fade_fn and 'label.set_tooltip(lab, "")' in fade_fn
    for destructive in (".delete(", ".remove(", ".clear(", "alert(", "f_trkEnd("):
        assert destructive not in fade_fn, f"mute helper must not perform {destructive}"

    # Only the already-existing Clean drawing-density branches gain MX Lite.
    for fragment in (
        "int otherLimit = compactView ? 1 : iLvN",
        "plotshape(iRib and not compactView",
        "if iTtLines and not compactView",
        "if iTtView and not compactView",
        "if iNwog and not compactView",
        "nIn < (compactView ? 1 : 2)",
        "for pass = 1 to (compactView ? 1 : iZN)",
    ):
        assert fragment in new_source, fragment
    assert "if barstate.islast and iPanel and (iDet == \"Simple\" or cleanView)" in new_source
    assert "if barstate.islast and iPanel and iDet == \"Full\" and not cleanView" in new_source

    # Positive controls: a changed setup gate or a destructive latest-only operation must fail.
    old_gate = "bool show = slOk and gN >= minG and (okWin or iOut == \"Dim\") and not duplicate"
    assert old_source.count(old_gate) == 1
    bad_gate = parse(old_source.replace(old_gate, old_gate.replace("gN >= minG", "gN > minG"), 1))
    assert dump(next(node for node in setup_body(bad_gate) if head(node).startswith("bool show ="))) != dump(
        next(node for node in setup_body(old) if head(node).startswith("bool show ="))
    ), "positive control missed a changed grade gate"
    bad_hide = parse(new_source.replace("f_stFade(oldSt, true)", "oldSt.lb.delete()", 1))
    bad_recent = next(node for node in shown_setup(bad_hide) if head(node) == "if mxLiteView and iMxRecent and sts.size() > 0")
    assert ".delete()" in unparse(bad_recent), "positive control missed destructive hide"
    bad_tracker = parse(new_source.replace("if t.tagVisible", "if true", 1))
    try:
        check_tracker_visibility(old, bad_tracker)
    except AssertionError:
        pass
    else:
        raise AssertionError("positive control missed a tracker update to a hidden label")

    print("PASS: 3.64 MX Lite controls are display-only; Current/Clean, setup gate, preview, tracker outcomes and model helpers preserved")


if __name__ == "__main__":
    main()
