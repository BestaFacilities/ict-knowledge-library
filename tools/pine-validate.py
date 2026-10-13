#!/usr/bin/env python3
"""Policy validator for the Pine scripts in this repo — the offline fallback checker.

PRIMARY ORACLE (use it when it is available): `tools/pine-lint.sh`, a build of the open-source
Pine v6 language service whose diagnostics mirror TradingView's wording (CE10123 etc.). It is a
real type/scope checker and it is what found the 68 problems in the 2026-10-09 round (audit §11).
This file exists because that oracle has to be cloned and built, so it is not always on hand; the
rules below are the subset of what it caught that we can also prove statically. `pyne check` (the
pynescript ANTLR front-end) validates SYNTAX only — every one of those 68 passed `pyne check`.

Eleven rules, each motivated by a real failure we actually shipped and had to fix:

  LOOP-CLAMP   A counted `for i = a to b` takes its DIRECTION from a vs b and always runs at
               least once. `for i = array.size(x) - 1 to 0` on an EMPTY array therefore executes
               the body with i = -1, and array.get(x, -1) is a runtime "index out of bounds" (or,
               for the `m to m-1` shape, a *valid* index that silently corrupts a stat). The
               compiler accepts it; only the data can reject it. Every such loop must open with a
               two-sided clamp and a `continue`.
  TABLE-CELL   table.cell(t, col, row, ...) must stay inside t's table.new(columns, rows) grid —
               TradingView reports these as a generic "error on line N", often 50+ lines off.
  ARR-LEN      A literal index into a fixed-size array must be inside it.
  COLL-SUGAR   `arr[i]` on a GLOBAL array read from INSIDE a user-defined function types as the
               array, not the element: TV answers "cannot apply '==' to array<int> and int". The
               sugar is fine at global scope and fine when the array is a parameter — so either
               pass the collection in, or write array.get(). This one cost 62 errors.
  FORWARD-REF  A global is visible only AFTER its declaration line, including from inside
               functions. `group=grpR` where grpR is declared eight lines lower is CE10272
               "Undeclared identifier" — and every input after it cascades.
  ARITY        A call with fewer arguments than the declared parameters is "No value assigned to
               the 'l2' parameter". Pine v6 has no optional parameters for user functions.
  SHADOW       A local that reuses a global name silently cuts the block off from that global
               (v2's journal block declared `int jr = 0` over the global `var float[] jr` returns
               array, and the fix exposed a `jr + 1` that had to be re-pointed deliberately).
  TYPO         A denylist of the `barstate.*` member spellings we have personally mistyped
               (barstate.is_last does not exist; barstate.islast does). Narrow on purpose: an
               allowlist built from memory of the spec would flag valid code.

Run `--selftest` to confirm the rules still fire — a checker whose control passes clean is
decoration, and a rule that flags everything is the same failure wearing a different hat.

Usage:  python3 tools/pine-validate.py tools/*.pine
        python3 tools/pine-validate.py --selftest
"""
import re
import os
import os
import sys

FOR = re.compile(r"^(\s*)for\s+(\w+)\s*=\s*(.+?)\s+to\s+(.+?)\s*$")
ARR_IDX = re.compile(r"array\.(?:get|set|insert|remove)\(\s*([A-Za-z_]\w*)\s*,\s*(\w+)\b")
PUSH = re.compile(r"array\.(?:push|unshift)\(\s*([A-Za-z_]\w*)\s*[,)]")
POP = re.compile(r"array\.(?:pop|shift)\(\s*([A-Za-z_]\w*)\s*\)")
TNEW = re.compile(r"(\w+)\s*=\s*table\.new\([^)]*?,\s*(\d+)\s*,\s*(\d+)\s*[,)]", re.S)
TCELL = re.compile(r"table\.cell\(\s*(\w+)\s*,\s*(\w+|\d+)\s*,\s*(\w+|\d+)")
FIXED = re.compile(r"(\w+)\s*=\s*array\.new_(?:int|float|bool|string|color)\((\d+)\s*[,)]")
FIXED_IX = re.compile(r"array\.get\(\s*(\w+)\s*,\s*(\d+)\s*\)")

COLL_DECL = re.compile(r"^(?:var\s+)?(?:const\s+|simple\s+|series\s+)?"
                       r"(?:array<[^>]+>|map<[^>]+>|matrix<[^>]+>| udtype\w*|"
                       r"[\w.]+\[\]?)\s+(\w+)\s*=\s*(array\.|matrix\.|map\.|$)", re.M)
COLL_DECL2 = re.compile(r"^(?:var\s+)?(\w+\[\]|\w*(?:array|map|matrix)<[^>]+>)\s+(\w+)\s*=", re.M)
GDECL = re.compile(r"^((?:var|const|simple|series)\s+)*(?:[\w.]+(?:<[^>]+>)?(?:\[\])?\s+)?(\w+)\s*(?::?=)\s*", re.M)
# A head that starts with a control word is not a declaration, and `==` is not `=`: `if pDir == -1`
# and `for j = n - 1 to 0` both looked like declarations of pDir / j to a bare `name =` regex.
GDECL0 = re.compile(r"^(?:var\s+|const\s+|simple\s+|series\s+)*(?:[\w.]+(?:<[^>]+>)?(?:\[\])?\s+)?(\w+)\s*=(?!=)")
LOCAL_DECL = re.compile(r"^(?:(?:var|const|simple|series|type)\s+)?(?:[\w.]+(?:<[^>]+>)?(?:\[\])?\s+)?(\w+)\s*=(?!=)")
CTRL_WORDS = ("if", "for", "while", "switch", "else", "and", "or", "import", "export", "method")
FUNC_DEF = re.compile(r"^(\w+)\s*\(([^)]*)\)\s*(?:=>|\bimport\b)")
BARSTATE_TYPO = re.compile(r"\bbarstate\.(is_last|is_first|is_confirmed|is_realtime|isLast|isConfirmed|isRealtime|isLogged|historyReduced)\b")


def code_lines(lines):
    """Comments AND string contents blanked, so neither prose nor a quoted "a" can trigger a
    rule. Without the string pass this checker reported a forward reference for the letter inside
    `input.string("a", ...)` - a checker defect, not a code defect."""
    out = []
    for ln in lines:
        if re.match(r"^\s*//", ln):
            out.append(" " * len(ln))
            continue
        ln = re.sub(r'"(?:[^"\n]|\.)*"', lambda m: '"' + " " * (len(m.group(0)) - 2) + '"', ln)
        k = ln.find("//")
        if k >= 0:  # trailing comments are prose, not code: v2's `// the delivery plot is a
            ln = ln[:k] + " " * (len(ln) - k)  # full-width line` fired FORWARD-REF for `delivery`
        out.append(ln)
    return out


def _split_top(s, seps=","):
    """Split on `seps` at paren/bracket/quote depth 0."""
    parts, depth, cur, q = [], 0, "", False
    for ch in s:
        if q:
            cur += ch
            if ch == '"':
                q = False
            continue
        if ch == '"':
            q = True
            cur += ch
        elif ch in "([":
            depth += 1
            cur += ch
        elif ch in ")]":
            depth -= 1
            cur += ch
        elif ch in seps and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p for p in parts if p.strip() != ""]


def scan_structure(lines):
    """globals: name -> first declaration line index. funcs: name -> (line, params, body range)."""
    globals_, funcs, i = {}, [], 0
    code = code_lines(lines)
    while i < len(code):
        ln = code[i]
        if ln[:1] not in ("", " ", "\t"):
            m = FUNC_DEF.match(ln)
            if m:
                params = [p.strip().split()[-1] for p in _split_top(m.group(2)) if p.strip()]
                j = i + 1
                while j < len(code) and (code[j].strip() == "" or code[j][:1].isspace()):
                    if code[j].strip() == "" and j + 1 < len(code) and code[j + 1][:1] not in (" ", "\t", ""):
                        break
                    j += 1
                funcs.append((m.group(1), i, params, i + 1, j))
                i = j
                continue
            g = None if ln.split(" ")[0] in CTRL_WORDS else GDECL0.match(ln)
            if g and g.group(1) not in globals_:
                globals_[g.group(1)] = i
        i += 1
    return globals_, funcs


def collections(lines):
    """Names declared with an array/map/matrix type, at column 0."""
    code = code_lines(lines)
    out = set()
    for n, ln in enumerate(code):
        if ln[:1] in ("", " ", "\t"):
            continue
        for rx in (COLL_DECL2, GDECL0):
            m = rx.match(ln)
            if m and (re.search(r"array<|map<|matrix<|\[\]", ln) or re.search(r"=\s*array\.(new|from)", ln)):
                out.add(m.group(1) if rx is GDECL0 else m.group(2))
    return out


def coll_sugar(lines):
    """`arr[i]` on a collection is only legal at GLOBAL scope. Measured against the v6 language
    service: `v = a[0]` at column 0 is clean, and the same read inside a `for` body, an `if` body
    or a UDF types as the ARRAY (`cannot apply '==' to array<int> and int`) - passing the array in
    as a parameter is clean again. 62 of the 63 overlay errors were this. Rule: array.get/array.set
    everywhere inside a block."""
    cols = collections(lines)
    if not cols:
        return []
    code = code_lines(lines)
    pat = re.compile(r"(?<![\w.])(" + "|".join(re.escape(c) for c in sorted(cols)) + r")\[(?!:)([^\[\]]+)\]")
    out = []
    for n, ln in enumerate(code):
        if not ln[:1].isspace():
            continue                      # column 0: the sugar is legal there, measured
        for m in pat.finditer(ln):
            out.append(f"{n + 1:5d}  COLL-SUGAR  {m.group(1)}[{m.group(2)}] inside a block: a "
                       f"collection indexed below column 0 types as the collection itself - write "
                       f"array.get/array.set (or take it as a function parameter)")
    return out


def forward_refs(lines):
    """Any name read above its own column-0 declaration line (TV resolves strictly top-down)."""
    globals_, funcs = scan_structure(lines)
    code = code_lines(lines)
    kw = {"if", "for", "while", "else", "switch", "box", "label", "line", "table", "array", "math",
          "str", "color", "input", "ta", "request", "barstate", "syminfo", "timeframe", "plot",
          "plotshape", "plotchar", "indicator", "strategy", "alertcondition", "var", "int",
          "float", "bool", "string", "color", "const", "simple", "series", "import", "export",
          "type", "method", "and", "or", "not", "na", "true", "false", "continue", "break",
          "return", "function", "_udt", "matrix", "map", "linefill", "hline", "plotcandle"}
    func_names = {f[0] for f in funcs}
    out = []
    for name, decl in sorted(globals_.items()):
        if name in kw or name in func_names or name.startswith("_"):
            continue
        rx = re.compile(r"(?<![\w.])" + re.escape(name) + r"(?![\w(])")
        for n in range(decl):
            if rx.search(code[n]) and n not in (decl,):
                out.append(f"{n + 1:5d}  FORWARD-REF  '{name}' used here, declared on line {decl + 1}: "
                           f"a global is only visible after its declaration line (CE10272)")
                break
    return out


def arity(lines):
    """Call-site argument count vs the user function's declared parameter count."""
    code = code_lines(lines)
    globals_, funcs = scan_structure(lines)
    out = []
    for fname, fline, params, b0, b1 in funcs:
        want = len(params)
        for n, ln in enumerate(code):
            if n == fline:
                continue
            for m in re.finditer(r"(?<![\w.])" + re.escape(fname) + r"\(", ln):
                depth, k, args = 1, m.end(), ""
                while k < len(ln) and depth:
                    c = ln[k]
                    depth += (c == "(") - (c == ")")
                    args += c
                    k += 1
                if depth:      # call spans lines: not checkable with this scanner
                    continue
                got = len(_split_top(args[:-1])) if args.strip("()") else 0
                if got != want:
                    out.append(f"{n + 1:5d}  ARITY  {fname}() called with {got} args, declared with "
                               f"{want} - v6 user functions have no optional parameters")
    return out


def shadows(lines):
    """An indented declaration that reuses a global name."""
    globals_, funcs = scan_structure(lines)
    code = code_lines(lines)
    param_names = {p for _, _, ps, _, _ in funcs for p in ps}
    out = []
    for n, ln in enumerate(code):
        if not ln[:1].isspace():
            continue
        strip = ln.strip()
        if strip.split(" ")[0] in CTRL_WORDS:
            continue          # a test, not a declaration
        m = LOCAL_DECL.match(strip)
        if not m:
            continue
        name = m.group(1)
        if name in globals_ and name not in param_names and not name.startswith("_"):
            out.append(f"{n + 1:5d}  SHADOW  local '{name}' hides the global of the same name "
                       f"(declared line {globals_[name] + 1}) - the block cannot see the global any more")
    return out


def typos(lines):
    out = []
    for n, ln in enumerate(code_lines(lines)):
        for m in BARSTATE_TYPO.finditer(ln):
            out.append(f"{n + 1:5d}  TYPO  barstate.{m.group(1)} is not a member (v6 spells it "
                       f"islast / isconfirmed / isrealtime)")
    return out


def loop_clamp(lines):
    out = []
    for n, line in enumerate(lines):
        m = FOR.match(line)
        if not m:
            continue
        ind, var, start, end = m.groups()
        body, k = [], n + 1
        while k < len(lines):
            nxt = lines[k]
            if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= len(ind):
                break
            body.append(nxt)
            k += 1
        txt = "\n".join(body)
        arrays = {a for a, v in ARR_IDX.findall(txt) if v == var}
        if not arrays:
            continue
        # Only size-derived bounds can be empty or self-referential; a literal `for k = 0 to 5`
        # over a fixed-size array is safe by construction and needs no clamp.
        if not re.search(r"array\.size\(|\bsz\b|\bm\b|size", start + " " + end):
            continue
        head = "\n".join(body[:14])
        low = re.search(rf"\bif\b[^\n]*\b{var}\s*<\s*(?:0|\w+)", head)
        high = re.search(rf"\b{var}\s*>=\s*(?:array\.size\(|\w+)", head)
        if not (low and high and re.search(r"\bcontinue\b", head)):
            out.append(f"{n + 1:5d}  LOOP-CLAMP  for {var} indexes {sorted(arrays)}; body must "
                       f"open with `if {var} < 0 or {var} >= <size> / continue`")
    return out


def table_cells(lines):
    txt = "\n".join(lines)
    grids = {t: (int(c), int(r)) for t, c, r in TNEW.findall(txt)}
    out = []
    for n, line in enumerate(lines):
        for t, c, r in TCELL.findall(line):
            if t not in grids:
                continue
            cols, rows = grids[t]
            try:
                ci, ri = int(c), int(r)
            except ValueError:
                continue  # variable col/row: handled by the row-cursor convention below
            if ci >= cols or ri >= rows:
                out.append(f"{n + 1:5d}  TABLE-CELL  {t} cell ({ci},{ri}) outside {cols}x{rows}")
    return out, grids


def fixed_arrays(lines):
    txt = "\n".join(lines)
    sizes = {n: int(v) for n, v in FIXED.findall(txt)}
    out = []
    for n, line in enumerate(lines):
        for name, ix in FIXED_IX.findall(line):
            if name in sizes and int(ix) >= sizes[name]:
                out.append(f"{n + 1:5d}  ARR-LEN  literal index {ix} into {name} (size {sizes[name]})")
    return out, sizes


def _lockstep_unused(lines):
    """Groups of arrays that are pushed and popped together must stay equal in count."""
    txt = "\n".join(lines)
    pushes, pops = {}, {}
    for m in PUSH.finditer(txt):
        pushes[m.group(1)] = pushes.get(m.group(1), 0) + 1
    for m in POP.finditer(txt):
        pops[m.group(1)] = pops.get(m.group(1), 0) + 1
    out = []
    fams = {}
    for name in sorted(set(pushes) | set(pops)):
        fams.setdefault(re.match(r"([a-z]+)", name).group(1), []).append(name)
    for fam, names in fams.items():
        if len(names) < 3:
            continue
        bad = {nm: (pushes.get(nm, 0), pops.get(nm, 0)) for nm in names
               if pushes.get(nm, 0) != pops.get(nm, 0)}
        if bad:
            out.append(f"       LOCKSTEP  family '{fam}*' push/pop mismatch: {bad} "
                       f"(siblings push {pushes.get(names[0], 0)})")
    return out


def nospeech(lines):
    """Comments stripped, string CONTENTS kept - the three literal-aware rules need to read what is
    inside the quotes, and every other rule must not."""
    out = []
    for ln in lines:
        if re.match(r"^\s*//", ln):
            out.append(" " * len(ln))
            continue
        k = ln.find("//")
        out.append(ln[:k] if k >= 0 else ln)
    return out


FMT_LEAK = re.compile(r"%[sd]\b|%\(|(?<!\{)\{(?!\{)[^{}]{0,24}\}(?!\})|\.format\(|__\w+__")


def template_leaks(lines):
    """TEMPLATE-LEAK  a Python/C format placeholder sitting inside a Pine string literal. This is the
    bug that shipped for weeks: the v1 file arrived with `if preset == "%s"` from whoever's notebook it
    was pasted out of, so that whole rung of the timeframe ladder was unreachable and the panel still
    printed the tier name as if it had applied."""
    out = []
    for n, ln in enumerate(nospeech(lines)):
        for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', ln):
            bad = FMT_LEAK.search(m.group(1))
            if bad:
                out.append(f"{n + 1:5d}  TEMPLATE-LEAK  {m.group(0)} carries the placeholder "
                           f"{bad.group(0)!r}: a Pine string is a literal, so this value can never be "
                           f"produced or matched - it is a paste artifact")
    return out


TAUTO_OR = re.compile(r"\bor\s+true\b|\band\s+false\b")


def tautologies(lines):
    """TAUTOLOGY  a boolean term that cannot fail. `(not clockOk or true)` reads like a gate, is
    always true, and was quietly defeating the after-hours cutoff on iFVG entries while looking like it
    enforced it. Matched on code only (strings blanked) so prose about 'always true' cannot trip it."""
    out = []
    for n, ln in enumerate(code_lines(lines)):
        m = TAUTO_OR.search(ln)
        if m:
            out.append(f"{n + 1:5d}  TAUTOLOGY  '{m.group(0).strip()}' makes the whole condition "
                       f"{'unfailable' if m.group(0).startswith('or') else 'unsatisfiable'} - either "
                       f"drop the term or make it a real switch")
    return out


OPTS_RX = re.compile(r"^(\w+)\s*=\s*input\.string\((.*)\)")
LIT_RX = re.compile(r'"([^"]*)"')
CMP_RX = re.compile(r'\b([A-Za-z_]\w*)\s*(?:==|!=)\s*"([^"]*)"')
LAD_RX = re.compile(r'^\s*(?:if|else if)\s+([A-Za-z_]\w*)\s*==\s*"([^"]*)"')
ASS_RX = re.compile(r"^\s*(?:var\s+)?(?:string|int|float|bool)?\s*(\w+)\s*=\s*(.+)$")


def ladder_gaps(lines):
    """LADDER-GAP  an if/else-if ladder that dispatches on a string input, checked against that input's
    options in both directions: an option no rung ever matches (silently selects nothing, while the UI
    offers it and the panel reports it), and a rung no option can ever select (dead code that reads like a
    tier). Ladders are only judged for inputs they actually dispatch on, so a mode string whose middle
    value is only ever tested with != (ifvgMode) is not accused."""
    code = nospeech(lines)
    opts, cmts, chain, refs = {}, {}, {}, {}
    for ln in code:
        m = OPTS_RX.match(ln.strip())
        if m and "options=[" in m.group(2):
            inside = m.group(2).split("options=[", 1)[1].split("]", 1)[0]
            opts[m.group(1)] = [x for x in LIT_RX.findall(inside)]
        for cm in CMP_RX.finditer(ln):
            cmts.setdefault(cm.group(1), set()).add(cm.group(2))
        lm = LAD_RX.match(ln)
        if lm:
            chain.setdefault(lm.group(1), set()).add(lm.group(2))
        am = ASS_RX.match(ln)
        if am:
            refs[am.group(1)] = am.group(2)
    out = []
    for var, choices in opts.items():
        reach = {var}
        for _ in range(3):  # follow one or two derivation hops (preset -> tier)
            for v, rhs in refs.items():
                if v in reach or not re.search(r"\b%s\b" % re.escape(var), rhs or ""):
                    continue
                if any(re.search(r"\b%s\b" % r, rhs or "") for r in reach):
                    reach.add(v)
        rung = set().union(*[chain[v] for v in reach if v in chain]) if any(v in chain for v in reach) else set()
        # A `if x == "a" ... else <residual>` is not a dispatch table: the residual IS the remaining
        # option, so accusing it of ignoring an option would be wrong (crtTgt's "Opposite bound",
        # crtFri's "Off"). Require a real ladder - three or more named rungs - before judging coverage.
        if len(rung) < 3:
            continue
        compared = set().union(*[cmts[v] for v in reach if v in cmts]) if any(v in cmts for v in reach) else set()
        for c in choices:
            if c not in compared and c not in rung:
                out.append(f"    0  LADDER-GAP  option {c!r} of {var} is never matched by any branch "
                           f"(dispatch vars {sorted(reach & set(chain))}) - picking it in the UI changes "
                           f"nothing and the script cannot tell you so")
        for c in rung:
            if c not in choices:
                out.append(f"    0  LADDER-GAP  a branch compares against {c!r}, which is not an option "
                           f"of {var} - that rung is unreachable (placeholder, typo, or a tier removed "
                           f"from the list and left behind)")
    return out


def check(lines):
    findings = loop_clamp(lines)
    tc, grids = table_cells(lines)
    fa, sizes = fixed_arrays(lines)
    new = coll_sugar(lines) + forward_refs(lines) + arity(lines) + shadows(lines) + typos(lines)
    new += tautologies(lines) + template_leaks(lines) + ladder_gaps(lines)
    return findings + tc + fa + new, grids, sizes


CONTROL = '''//@version=6
indicator("control")
x = input.string("a", "A", group=grpLate)
grpLate = "======= Late ======="
var float[] a = array.new_float()
var float[] b = array.new_float()
var table tb = table.new(position.top_right, 2, 2)
f_two(int p1, int p2) =>
    p1 + p2
f_glob() =>
    array.size(a) + a[0]
c = f_two(1)
if barstate.islast
    y = a[0] + 1.0
    float a = 2.0
    for i = array.size(a) - 1 to 0
        x = array.get(a, i)
    for j = 0 to array.size(b) - 1
        array.set(b, j, 1.0)
    table.cell(tb, 4, 9, "out of grid")
    w = not inKz or true
disp = input.string("a", "D", options=["a", "b", "orphan"])
string dsel = disp
if dsel == "a"
    q = 1
else if dsel == "b"
    q = 2
else if dsel == "%s"
    q = 3
    if barstate.is_last
        x := 1
'''

# SHADOW is 2 because `x = array.get(a, i)` inside the control's loop is itself a local shadow of
# the global x - a true positive, not a checker defect: inside a block `name = value` DECLARES.
EXPECT = {"LOOP-CLAMP": 2, "TABLE-CELL": 1, "COLL-SUGAR": 2, "FORWARD-REF": 1,
          "ARITY": 1, "SHADOW": 2, "TYPO": 1, "TAUTOLOGY": 1, "TEMPLATE-LEAK": 1, "LADDER-GAP": 2}


LITERAL_RULES = {"TAUTOLOGY", "TEMPLATE-LEAK", "LADDER-GAP"}
CONTROL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "ladder-bug.control.pine")


def selftest():
    f, _, _ = check(CONTROL.split("\n"))
    kinds = [x.split()[1] for x in f]
    ok = all(kinds.count(k) == n for k, n in EXPECT.items()) and len(f) == sum(EXPECT.values())
    for line in f:
        print("  control:", line)
    print(f"  selftest: {'PASS' if ok else 'FAIL'} (expected {EXPECT}, got {kinds})")
    # The synthetic fixture is necessary but not sufficient: a rule tuned until it likes its own
    # fixture proves nothing. This control is the actual broken line from the actual shipped file -
    # the 3min rung of the timeframe ladder, left as `== "%s"` by the patch that renamed preset->tier
    # (audit s16) - so the check is anchored to a defect that really reached a chart.
    real = 0
    try:
        rf, _, _ = check(open(CONTROL_FILE, encoding="utf-8").read().split("\n"))
        real = len([x for x in rf if x.split()[1] in LITERAL_RULES])
        for line in rf:
            print("  real control:", line)
    except OSError as e:
        print(f"  real control: MISSING {CONTROL_FILE} - the anchor of this selftest is not optional")
    if real < 3:
        print(f"  selftest: FAIL (real-code control must yield >=3 literal-class findings, got {real})")
        return 1
    return 0 if ok else 1


def main():
    args = sys.argv[1:]
    if not args or args == ["--selftest"]:
        sys.exit(selftest())
    bad = 0
    for path in args:
        f, grids, sizes = check(open(path, encoding="utf-8").read().split("\n"))
        if os.sep + "archive" + os.sep in path:
            kept = [x for x in f if x.split()[1] not in LITERAL_RULES]
            if len(kept) != len(f):
                print(f"{path}: {len(f) - len(kept)} literal-class finding(s) suppressed - archived "
                      f"baseline, kept byte-identical on purpose")
            f = kept
        meta = f"tables={grids} fixed={ {k: v for k, v in sizes.items() if v < 30} }"
        print(f"{path}" + (f"   {meta}" if grids else ""))
        for line in f:
            print("   ", line)
        bad += len(f)
        if not f:
            print("    CLEAN")
    print(f"{'FAIL' if bad else 'OK'}: {bad} finding(s) across {len(args)} file(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
