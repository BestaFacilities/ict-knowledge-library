#!/usr/bin/env python3
"""AST regression: 3.58's optional row must not rewrite the 3.57 setup engine.

Run with hoox-pyne's parser installed: python tools/tests/test_snm_358_noninterference.py
The fixed base commit is the pushed 3.57 source on this branch; no donor code is used.
This proves only that f_preview and the original f_setup nodes are unchanged, not
that TradingView compiled tokens, live alerts, or visual rendering pass.
"""
from pathlib import Path
import subprocess

from pynescript.ast import dump, parse, unparse

BASE = "458dbf8cd0b48a14fcd586195209d66e6c417d96"
ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "tools/snm-plus.pine"


def get_function(tree, name):
    nodes = [node for node in tree.body if getattr(node, "name", None) == name]
    assert len(nodes) == 1, (name, len(nodes))
    return nodes[0]


def setup_without_display(tree):
    """Project away ONLY the new read-only state block, retaining all prior nodes."""
    func = get_function(tree, "f_setup")
    heads = [unparse(node).split("\n", 1)[0] for node in func.body]
    display = [i for i, head in enumerate(heads) if head == "if iStageRow"]
    assert len(display) <= 1, display
    return [dump(node) for i, node in enumerate(func.body) if i not in display]


def main():
    old = subprocess.check_output(["git", "show", BASE + ":tools/snm-plus.pine"], cwd=ROOT, text=True)
    new = CURRENT.read_text()
    assert 'input.bool(false, "Show setup state row (study)"' in new
    old_tree = parse(old)
    new_tree = parse(new)
    assert dump(get_function(old_tree, "f_preview")) == dump(get_function(new_tree, "f_preview"))
    original = setup_without_display(old_tree)
    assert original == setup_without_display(new_tree), "f_setup changed outside state-row instrumentation"
    # Positive control: an actual setup-grade gate change MUST be detected.
    probe = 'bool show = slOk and gN >= minG and (okWin or iOut == "Dim") and not duplicate'
    assert old.count(probe) == 1
    broken = parse(old.replace(probe, probe.replace("gN >= minG", "gN > minG"), 1))
    assert original != setup_without_display(broken), "positive control failed to catch grade-gate change"
    print("PASS: f_preview and f_setup baseline AST unchanged; grade-gate positive control fires")


if __name__ == "__main__":
    main()
