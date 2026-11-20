#!/usr/bin/env python3
"""AST regression for SNM+ 3.65's display-only checklist-clarity pass.

Run with hoox-pyne installed: python tools/tests/test_snm_checklist_clarity.py
The test compares the active 3.64 source with 3.65. Stage 2 only relabels the
checklist panel: a LAST SETUP section header, NOW row labels, an explicit
"n/a" for disabled checks (TTFM Off, SMT Off), and "–" for no data yet. It
must not change setup qualification, grades, D/T/E meanings, targets, alerts
or detector logic. It cannot verify TradingView rendering or replay.
"""
from pathlib import Path
import subprocess

from pynescript.ast import dump, parse, unparse

BASE = "fb68de1"  # SNM+ 3.64 immediately before checklist clarity
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


def panel_block(tree, header):
    blocks = [node for node in tree.body if head(node) == header]
    assert len(blocks) == 1, header
    return blocks[0]


def cell_rows(block):
    """(row, col, text) for every tb.cell(...) call in a panel block."""
    rows = []
    for node in block.value.body:
        text = unparse(node)
        if "tb.cell(" not in text:
            continue
        # tb.cell(col, row, text, ...) — the first two args are literals or
        # loop variables; skip non-literal rows (the Full-panel check loop).
        args = text[text.index("tb.cell(") + len("tb.cell("):].split(",")
        try:
            col = int(args[0].strip())
            row = int(args[1].strip())
        except ValueError:
            continue
        rows.append((row, col, text))
    return rows


def main():
    old_source = source_at(BASE, "tools/snm-plus.pine")
    new_source = CURRENT.read_text()
    old = parse(old_source)
    new = parse(new_source)

    assert 'indicator("SNM+ 3.67", shorttitle = "SNM+ 3.67"' in new_source

    # Non-display logic is untouched: every helper except f_setup (whose TTFM
    # checklist value changes below) and the setup gate are identical.
    for name in ("f_preview", "f_ck", "f_gT", "f_trkEnd", "f_sweep", "f_draw", "f_edge"):
        assert dump(function(old, name)) == dump(function(new, name)), f"helper changed: {name}"
    old_gate = next(node for node in setup_body(old) if head(node).startswith("bool show ="))
    new_gate = next(node for node in setup_body(new) if head(node).startswith("bool show ="))
    assert dump(old_gate) == dump(new_gate), "setup grade/window/dedup gate changed"

    # The only setup-body change is the TTFM checklist value: Off now reports
    # 3 (not assessed) instead of 0 (fail). Everything else is byte-identical.
    old_pv = [node for node in shown_setup(old) if head(node).startswith("pv.push(")]
    new_pv = [node for node in shown_setup(new) if head(node).startswith("pv.push(")]
    assert len(old_pv) == len(new_pv) == 8
    for o, n in zip(old_pv, new_pv):
        if "ttOk" in head(o):
            assert 'iTtF == "Off" ? 3 : ttOk ? 1 : 0' in unparse(n), "TTFM Off must be not-assessed (3)"
        else:
            assert dump(o) == dump(n), f"checklist value changed: {head(o)}"
    assert 'pv.push(iTtF == "Off" ? 3 : ttOk ? 1 : 0)' in new_source
    # SMT Off already reported 2 (not applicable) and stays that way.
    assert 'pv.push(smtOn ? (smtP ? 1 : 0) : 2)' in new_source

    # Panel: 2 x 21 table, LAST SETUP header, NOW rows, explicit states.
    assert "var table tb = table.new(position.bottom_right, 2, 21, border_width = 0)" in new_source
    assert "tb.clear(0, 0, 1, 20)" in new_source
    simple = panel_block(new, 'if barstate.islast and iPanel and (iDet == "Simple" or cleanView)')
    full = panel_block(new, 'if barstate.islast and iPanel and iDet == "Full" and not cleanView')
    for block in (simple, full):
        rows = cell_rows(block)
        texts = [t for _, _, t in rows]
        assert any('"LAST SETUP"' in t for t in texts), "LAST SETUP header missing"
        assert any('"NOW"' in t for t in texts), "NOW row label missing"
        assert not any('"Now"' in t for t in texts), "old 'Now' label must be gone"
        # LAST SETUP header sits directly under the SNM+ header row.
        last_row = max(r for r, _, t in rows if '"LAST SETUP"' in t)
        assert last_row == 1
    # Full panel: NOW is the last row; Simple panel: NOW follows Today.
    full_rows = cell_rows(full)
    assert max(r for r, _, t in full_rows if '"NOW"' in t) == 20
    simple_rows = cell_rows(simple)
    assert max(r for r, _, t in simple_rows if '"NOW"' in t) == 7
    # Explicit states: n/a for disabled checks, – for no data yet.
    assert 'v == 3 ? "n/a"' in new_source
    assert '"  –"' in new_source
    # The Now-row tooltip still documents the confirmed-bar priority.
    assert "Now = current close, else PREV CLOSE (1 bar), else live wait/preview. ELIGIBLE is not alert delivery." in new_source

    # Positive controls: dropping the n/a state or the LAST SETUP header must fail.
    no_na = parse(new_source.replace('v == 3 ? "n/a" : ', "", 1))
    assert 'v == 3 ? "n/a"' not in unparse(panel_block(no_na, 'if barstate.islast and iPanel and iDet == "Full" and not cleanView'))
    no_header = parse(new_source.replace('"LAST SETUP"', '"LAST"'))
    assert not any('"LAST SETUP"' in t for _, _, t in cell_rows(panel_block(no_header, 'if barstate.islast and iPanel and iDet == "Full" and not cleanView')))
    # ... and the LAST SETUP header must sit directly under the SNM+ header row.
    full_rows = cell_rows(full)
    assert max(r for r, _, t in full_rows if '"LAST SETUP"' in t) == 1

    print("PASS: 3.65 checklist clarity is display-only; LAST SETUP/NOW labels, n/a and – states; setup/grade/alert logic preserved")


if __name__ == "__main__":
    main()
