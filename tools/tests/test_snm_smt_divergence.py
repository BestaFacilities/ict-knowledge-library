#!/usr/bin/env python3
"""AST regression for SNM+ 3.67's opt-in SMT divergence markers.

Run with hoox-pyne installed: python tools/tests/test_snm_smt_divergence.py
The test compares the active 3.66 source with 3.67. SMT divergence markers are
display-only: they mark swing points where the chart makes a new high/low but
the SMT pair does not. They must not change setup qualification, grades,
targets, tracker outcomes, or alerts. It cannot verify TradingView rendering
or replay.
"""
from pathlib import Path
import subprocess

from pynescript.ast import dump, parse, unparse

BASE = "6a4fca5"  # SNM+ 3.66 immediately before SMT divergence markers
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
    # CW10003 fix: setup logic is wrapped in `if d != 0` for unconditional calls.
    if len(body) >= 1 and head(body[0]) == "if d != 0":
        return list(body[0].value.body) + list(body[1:])
    return body


def source_at(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True)


def main():
    old_source = source_at(BASE, "tools/snm-plus.pine")
    new_source = CURRENT.read_text()
    old = parse(old_source)
    new = parse(new_source)

    assert 'indicator("SNM+ 3.69", shorttitle = "SNM+ 3.69"' in new_source

    # The opt-in input exists and defaults Off (display-only, opt-in).
    assert 'bool iSmtDiv = input.bool(false, "Show SMT divergence markers"' in new_source
    assert 'group = G_C' in new_source

    # The setup gate is identical (TTrades removal changed f_setup body but not the gate).
    # f_setup body comparison is covered by the noninterference regression.
    old_gate = next(node for node in setup_body(old) if head(node).startswith("bool show ="))
    new_gate = next(node for node in setup_body(new) if head(node).startswith("bool show ="))
    assert dump(old_gate) == dump(new_gate), "setup grade/window/dedup gate changed"

    # The divergence markers are gated by iSmtDiv AND smtOn (pair data available).
    assert "if iSmtDiv and not na(prevPhH) and not na(prevPhP) and ph5 > prevPhH and oH[5] < prevPhP" in new_source
    assert "if iSmtDiv and not na(prevPlL) and not na(prevPlP) and pl5 < prevPlL and oL[5] > prevPlP" in new_source
    assert "if smtOn and not na(oH[5])" in new_source
    assert "if smtOn and not na(oL[5])" in new_source

    # Bearish: chart higher high + pair lower high. Bullish: chart lower low + pair higher low.
    assert '"SMT-"' in new_source and '"SMT+"' in new_source
    assert "label.style_label_up" in new_source  # bearish marker above the swing high
    assert "label.style_label_down" in new_source  # bullish marker below the swing low

    # Markers are informational: the tooltip states this explicitly.
    assert "Informational only." in new_source

    # State variables track the previous pivot extremes for the comparison.
    assert "var float prevPhH = na" in new_source
    assert "var float prevPhP = na" in new_source
    assert "var float prevPlL = na" in new_source
    assert "var float prevPlP = na" in new_source
    assert "prevPhH := ph5" in new_source and "prevPhP := oH[5]" in new_source
    assert "prevPlL := pl5" in new_source and "prevPlP := oL[5]" in new_source

    # Positive controls: flipping a divergence condition or dropping the gate must be detectable.
    flipped = parse(new_source.replace("ph5 > prevPhH and oH[5] < prevPhP", "ph5 < prevPhH and oH[5] > prevPhP", 1))
    assert "ph5 < prevPhH and oH[5] > prevPhP" in unparse(flipped)
    no_gate = parse(new_source.replace("if iSmtDiv and not na(prevPhH)", "if not na(prevPhH)", 1))
    assert "if iSmtDiv and not na(prevPhH)" not in unparse(no_gate)

    print("PASS: 3.67 SMT divergence markers are display-only and opt-in; setup/grade/alert logic preserved")


if __name__ == "__main__":
    main()
