#!/usr/bin/env python3
"""Pine AST regression for SNM+ 3.64's display-only MX Lite pass.

Run with hoox-pyne installed: python tools/tests/test_snm_noninterference.py
The active setup/grade/alert baseline is 3.63. The projection omits the existing
read-only stage row plus this pass's setup-drawing construction, older-drawing
mute, and tracker-tag visibility bookkeeping. It retains the setup gate, tooltip,
tracker outcomes, UI/checklist state and alert AST. 3.60's one-bar
historical Now row is still guarded against the 3.59 AST. This is not TradingView
compilation, visual or live-alert verification.
"""
from pathlib import Path
import subprocess

from pynescript.ast import dump, parse, unparse

BASE = "b5d2cb7"  # SNM+ 3.63 immediately before MX Lite
ROW_BASE = "e53a2f4"
ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "tools/snm-plus.pine"


def function(tree, name):
    nodes = [node for node in tree.body if getattr(node, "name", None) == name]
    assert len(nodes) == 1, (name, len(nodes))
    return nodes[0]


def head(node):
    return unparse(node).split("\n", 1)[0]


def setup_body(tree):
    body = function(tree, "f_setup").body
    # 3.64 fix for CW10003 wraps the setup logic in `if d != 0` so the helper can be
    # called unconditionally; d == 0 is a no-op. Unwrap for the logic comparison.
    if len(body) >= 1 and head(body[0]) == "if d != 0":
        return list(body[0].value.body) + list(body[1:])
    return body


def projection(tree):
    """Keep setup/grade/tracker/alert logic; omit display construction and mute metadata."""
    nodes = []
    for node in setup_body(tree):
        name = head(node)
        if name == "if iStageRow" or name.startswith("bool edOk ="):
            continue
        if name != "if show":
            nodes.append(dump(node))
            continue
        children = node.value.body  # Expr(If(...)) in pynescript's real Pine AST
        heads = [head(c) for c in children]
        render = next(i for i, h in enumerate(heads) if h.startswith("color c ="))
        tracking = next(i for i, h in enumerate(heads) if h == "if iTrack and okWin")
        assert [head(x) for x in children[:6]][-1] == "string gT = f_gT(gN)"
        # Includes signal registration, risk/grade calculation and the full setup tooltip.
        nodes.extend(dump(x) for x in children[:render])
        # These strings feed the setup label and outcome tracker, so they remain in the projection.
        nodes.extend(dump(x) for x in children[render:tracking] if head(x).startswith("string lbTxt =") or head(x) == 'bool pill = iLbl == "Pills"')
        # Outcome tracking, counters, D/T/E status, confluence rows and alert payload remain exact.
        nodes.extend(dump(x) for x in children[tracking:] if head(x) not in ("if mxLiteView and iMxRecent and sts.size() > 0", "nt.tagVisible := iSigShow"))
    return nodes


def stage_if(tree):
    blocks = [node for node in tree.body if head(node) == "if barstate.islast and iPanel and iStageRow"]
    assert len(blocks) == 1
    return blocks[0].value.body[0].value


def check_previous_close(old_tree, new_tree):
    """The added read-only branch must expire after exactly one bar and never win over this close."""
    before = stage_if(old_tree)
    now = stage_if(new_tree)
    assert unparse(now.test) == "ui.stageB == bar_index and barstate.isconfirmed"
    assert [dump(n) for n in now.body] == [dump(n) for n in before.body], "current-bar result or warning colour changed"
    assert len(now.orelse) == 1
    previous = now.orelse[0].value
    assert unparse(previous.test) == "ui.stageB >= 0 and ui.stageB == bar_index - 1"
    fixture = parse('stageText := "PREV CLOSE · " + ui.stageMsg\nstageColor := cMu\n')
    assert [dump(n) for n in previous.body] == [dump(n) for n in fixture.body], "historical row must be labelled and muted"
    assert [dump(n) for n in previous.orelse] == [dump(n) for n in before.orelse], "live wait/preview fallback changed"


def main():
    old = subprocess.check_output(["git", "show", BASE + ":tools/snm-plus.pine"], cwd=ROOT, text=True)
    new = CURRENT.read_text()
    assert 'input.bool(false, "Show setup state row (study)"' in new
    assert new.count("nt.tagVisible := iSigShow") == 1
    original = parse(old)
    current = parse(new.replace("nt.tagVisible := iSigShow", ""))  # display metadata only; checked by MX Lite regression
    assert dump(function(original, "f_preview")) == dump(function(current, "f_preview"))
    expected = projection(original)
    assert expected == projection(current), "non-display setup/grade/alert AST changed"
    # A real grade-gate regression must trip the projection's positive control.
    probe = 'bool show = slOk and gN >= minG and (okWin or iOut == "Dim") and not duplicate'
    assert old.count(probe) == 1
    broken = parse(old.replace(probe, probe.replace("gN >= minG", "gN > minG"), 1))
    assert expected != projection(broken), "positive control missed changed grade gate"
    alert_gate = "if okWin and (not hardB or iAlBlockedB)"
    assert old.count(alert_gate) == 1
    no_blocked_alert = parse(old.replace(alert_gate, "if okWin", 1))
    assert expected != projection(no_blocked_alert), "positive control missed changed alert gate"
    row_old = subprocess.check_output(["git", "show", ROW_BASE + ":tools/snm-plus.pine"], cwd=ROOT, text=True)
    row_before = parse(row_old)
    check_previous_close(row_before, current)
    guard = "ui.stageB >= 0 and ui.stageB == bar_index - 1"
    assert new.count(guard) == 1
    too_long = parse(new.replace(guard, "ui.stageB >= 0 and ui.stageB >= bar_index - 1", 1))
    try:
        check_previous_close(row_before, too_long)
    except AssertionError:
        pass
    else:
        raise AssertionError("positive control missed non-expiring historical row")
    print("PASS: unchanged 3.63 setup/grade/tracker/alert AST; grade, alert and 3.60 row-expiry mutations detected")


if __name__ == "__main__":
    main()
