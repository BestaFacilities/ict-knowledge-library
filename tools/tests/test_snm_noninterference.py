#!/usr/bin/env python3
"""Pine AST regression against shipped 3.57: only display text may change.

Run with hoox-pyne installed: python tools/tests/test_snm_noninterference.py
The 3.59 token-budget pass deliberately condenses Full tooltip text and removes
one dead display-only variable, so comparison excludes those nodes. The Simple
tooltip, setup/grade/alert paths and preview function must remain AST-identical.
This is not TradingView compilation, visual or live-alert verification.
"""
from pathlib import Path
import subprocess

from pynescript.ast import dump, parse, unparse

BASE = "458dbf8cd0b48a14fcd586195209d66e6c417d96"
ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "tools/snm-plus.pine"


def function(tree, name):
    nodes = [node for node in tree.body if getattr(node, "name", None) == name]
    assert len(nodes) == 1, (name, len(nodes))
    return nodes[0]


def head(node):
    return unparse(node).split("\n", 1)[0]


def projection(tree):
    """Keep all logic, excluding only the new stage block and Full tooltip text."""
    nodes = []
    for node in function(tree, "f_setup").body:
        name = head(node)
        if name == "if iStageRow" or name.startswith("bool edOk ="):
            continue
        if name != "if show":
            nodes.append(dump(node))
            continue
        children = node.value.body  # Expr(If(...)) in pynescript's real Pine AST
        heads = [head(c) for c in children]
        miss = next(i for i, h in enumerate(heads) if h == 'string miss2 = ""')
        render = next(i for i, h in enumerate(heads) if h.startswith("color c ="))
        assert [head(x) for x in children[:6]][-1] == "string gT = f_gT(gN)"
        nodes.extend(dump(x) for x in children[:6])  # setup registration, risk, grade
        # Reuse the same Simple plan and missing-check strings, before Full-only text.
        end = next(i for i, h in enumerate(heads) if h in ('if iDet == "Simple"', 'string tip = tipS'))
        nodes.extend(dump(x) for x in children[miss:end])
        nodes.extend(dump(x) for x in children[render:])  # drawings, tracker, grade, alert payload
    return nodes


def main():
    old = subprocess.check_output(["git", "show", BASE + ":tools/snm-plus.pine"], cwd=ROOT, text=True)
    new = CURRENT.read_text()
    assert 'input.bool(false, "Show setup state row (study)"' in new
    original = parse(old)
    current = parse(new)
    assert dump(function(original, "f_preview")) == dump(function(current, "f_preview"))
    expected = projection(original)
    assert expected == projection(current), "non-display setup/grade/alert AST changed"
    # A real grade-gate regression must trip the projection's positive control.
    probe = 'bool show = slOk and gN >= minG and (okWin or iOut == "Dim") and not duplicate'
    assert old.count(probe) == 1
    broken = parse(old.replace(probe, probe.replace("gN >= minG", "gN > minG"), 1))
    assert expected != projection(broken), "positive control missed changed grade gate"
    print("PASS: unchanged setup/grade/alert + Simple tooltip AST; mutated grade gate detected")


if __name__ == "__main__":
    main()
