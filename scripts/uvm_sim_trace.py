"""
Symbolic UVM 1.2 Mini-Simulator & Execution Trace Generator.

Parses SystemVerilog example suites (.sv/.svh + Makefiles) into a lightweight
control-flow AST and symbolically executes the UVM 1.2 lifecycle:
- Root test resolution (+UVM_TESTNAME / run_test)
- Top-down build_phase & connect_phase with factory overrides and config_db
- Bottom-up end_of_elaboration & start_of_simulation
- Cooperative time-wheel for run_phase / sub-phases (#delay, fork/join, loops, objections)
- Top-down extract / check / report / final phases
"""

import ast
import heapq
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# AST Nodes
# ---------------------------------------------------------------------------

@dataclass
class Stmt:
    line: int


@dataclass
class AssignNode(Stmt):
    lhs: str
    rhs: str


@dataclass
class DelayNode(Stmt):
    delay_expr: str


@dataclass
class SeqNode(Stmt):
    stmts: List[Stmt] = field(default_factory=list)


@dataclass
class ReportNode(Stmt):
    severity: str
    tag_expr: str
    msg_expr: str
    is_display: bool = False


@dataclass
class CallNode(Stmt):
    obj: str
    method: str
    args: str


@dataclass
class IfNode(Stmt):
    cond: str
    then_body: List[Stmt] = field(default_factory=list)
    else_body: List[Stmt] = field(default_factory=list)


@dataclass
class LoopNode(Stmt):
    kind: str  # for, repeat, foreach, while
    header: str
    body: List[Stmt] = field(default_factory=list)


@dataclass
class ForkNode(Stmt):
    join_kind: str  # join, join_any, join_none
    branches: List[List[Stmt]] = field(default_factory=list)


@dataclass
class MethodDef:
    name: str
    is_task: bool
    line: int
    params: List[str] = field(default_factory=list)
    body: List[Stmt] = field(default_factory=list)


@dataclass
class ClassDef:
    name: str
    base: str
    file: str
    line: int
    is_virtual: bool = False
    props: Dict[str, str] = field(default_factory=dict)
    methods: Dict[str, MethodDef] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Lexer / Line-Preserving Comment Stripper & Statement Splitter
# ---------------------------------------------------------------------------

def _strip_comments_preserve_lines(content: str) -> List[Tuple[int, str]]:
    """Return list of (1-based line_no, code_without_comments)."""
    out: List[Tuple[int, str]] = []
    in_block = False
    for idx, raw in enumerate(content.splitlines(), start=1):
        i = 0
        n = len(raw)
        buf: List[str] = []
        in_str = False
        while i < n:
            ch = raw[i]
            nxt = raw[i + 1] if i + 1 < n else ""
            if in_block:
                if ch == "*" and nxt == "/":
                    in_block = False
                    i += 2
                    continue
                i += 1
                continue
            if in_str:
                buf.append(ch)
                if ch == "\\" and i + 1 < n:
                    buf.append(nxt)
                    i += 2
                    continue
                if ch == '"':
                    in_str = False
                i += 1
                continue
            if ch == '"':
                in_str = True
                buf.append(ch)
                i += 1
                continue
            if ch == "/" and nxt == "/":
                break
            if ch == "/" and nxt == "*":
                in_block = True
                i += 2
                continue
            buf.append(ch)
            i += 1
        cleaned = "".join(buf).strip()
        if cleaned:
            out.append((idx, cleaned))
    return out


def _split_top_level_args(args_str: str) -> List[str]:
    """Split comma-separated arguments respecting parentheses, braces, and quotes."""
    args: List[str] = []
    buf: List[str] = []
    p_depth = 0
    b_depth = 0
    in_str = False
    i = 0
    while i < len(args_str):
        ch = args_str[i]
        if in_str:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(args_str):
                buf.append(args_str[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            buf.append(ch)
        elif ch == "(":
            p_depth += 1
            buf.append(ch)
        elif ch == ")":
            p_depth = max(0, p_depth - 1)
            buf.append(ch)
        elif ch == "{":
            b_depth += 1
            buf.append(ch)
        elif ch == "}":
            b_depth = max(0, b_depth - 1)
            buf.append(ch)
        elif ch == "," and p_depth == 0 and b_depth == 0:
            args.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        args.append(tail)
    return args


def _tokenize_statements(lines: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
    """
    Combine multi-line statements into single logical chunks while keeping
    structural keywords (begin, end, fork, join*, if, else, for, repeat, class, function, task)
    as clean tokens with their starting 1-based line number.
    """
    chunks: List[Tuple[int, str]] = []
    buf: List[str] = []
    start_ln = 0
    p_depth = 0
    b_depth = 0

    def flush():
        nonlocal buf, start_ln, p_depth, b_depth
        if buf:
            joined = " ".join(buf).strip()
            if joined:
                chunks.append((start_ln, joined))
        buf = []
        start_ln = 0
        p_depth = 0
        b_depth = 0

    for ln, txt in lines:
        # Ignore preprocessor directives except macros
        if txt.startswith("`include") or txt.startswith("`ifndef") or txt.startswith("`define") or txt.startswith("`endif"):
            flush()
            continue

        if not buf:
            start_ln = ln

        buf.append(txt)
        # Count parens/braces outside strings
        in_str = False
        i = 0
        while i < len(txt):
            c = txt[i]
            if in_str:
                if c == "\\":
                    i += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == "(":
                    p_depth += 1
                elif c == ")":
                    p_depth -= 1
                elif c == "{":
                    b_depth += 1
                elif c == "}":
                    b_depth -= 1
            i += 1

        joined_now = " ".join(buf).strip()
        is_struct = bool(re.match(
            r'^(?:virtual\s+)?(?:class|endclass|function|endfunction|task|endtask|module|endmodule|package|endpackage|initial|begin|end|fork|join|join_any|join_none|else)\b',
            joined_now
        ))
        is_cond_head = bool(re.match(r'^(?:if|else\s+if|for|repeat|foreach|while)\s*\(', joined_now))
        is_macro_call = joined_now.startswith("`uvm_") and (
            joined_now.endswith(")") or bool(re.match(r'^`uvm_\w+$', joined_now))
        )

        if p_depth <= 0 and b_depth <= 0:
            if joined_now.endswith(";") or is_struct or is_macro_call or (is_cond_head and joined_now.endswith(")")):
                flush()
            elif joined_now.endswith("begin") and is_cond_head:
                flush()

    flush()
    return chunks


# ---------------------------------------------------------------------------
# AST Builder
# ---------------------------------------------------------------------------

RE_REPORT_MACRO = re.compile(r'^`uvm_(info|warning|error|fatal)\s*\((.*)\)\s*;?$', re.S)
RE_REPORT_CALL = re.compile(r'^(?:[a-zA-Z_]\w*\.)?uvm_report_(info|warning|error|fatal)\s*\((.*)\)\s*;?$', re.S)
RE_DISPLAY_CALL = re.compile(r'^\$(?:display|write)\s*\((.*)\)\s*;?$', re.S)
RE_DELAY = re.compile(r'^#\s*\(?([a-zA-Z0-9_.\s+\-*/]+)\)?\s*;?$')
RE_CALL = re.compile(r'^(?:([a-zA-Z_]\w*(?:\s*::\s*[a-zA-Z_]\w*|(?:\.[a-zA-Z_]\w*)+)?(?:#\([^)]*\))?)\s*(?:\.|::))?([a-zA-Z_]\w*)\s*\((.*)\)\s*;?$', re.S)
RE_ASSIGN = re.compile(r'^(?:(?:static\s+|int\s+|string\s+|bit\s+|logic\s+|uvm_\w+\s+)*)?([a-zA-Z_]\w*)\s*=\s*(.+?)\s*;$')


def _parse_single_stmt(ln: int, txt: str) -> Optional[Stmt]:
    s = txt.strip()
    if not s or s == ";":
        return None

    m_rep = RE_REPORT_MACRO.match(s)
    if m_rep:
        args = _split_top_level_args(m_rep.group(2))
        tag = args[0] if len(args) >= 1 else '"INFO"'
        msg = args[1] if len(args) >= 2 else '""'
        return ReportNode(line=ln, severity=f"UVM_{m_rep.group(1).upper()}", tag_expr=tag, msg_expr=msg)

    m_rc = RE_REPORT_CALL.match(s)
    if m_rc:
        args = _split_top_level_args(m_rc.group(2))
        tag = args[0] if len(args) >= 1 else '"REPORT"'
        msg = args[1] if len(args) >= 2 else '""'
        return ReportNode(line=ln, severity=f"UVM_{m_rc.group(1).upper()}", tag_expr=tag, msg_expr=msg)

    m_disp = RE_DISPLAY_CALL.match(s)
    if m_disp:
        args = _split_top_level_args(m_disp.group(1))
        msg = args[0] if args else '""'
        if len(args) > 1:
            msg = f"$sformatf({m_disp.group(1)})"
        return ReportNode(line=ln, severity="UVM_INFO", tag_expr='"STDOUT"', msg_expr=msg, is_display=True)

    m_del = RE_DELAY.match(s)
    if m_del:
        return DelayNode(line=ln, delay_expr=m_del.group(1).strip())

    # Inline delay before statement, e.g. `#15 p = gen1.get_packet();`
    m_inline_del = re.match(r'^#\s*(\([^)]+\)|[a-zA-Z0-9_.]+)\s+(.+)$', s, re.S)
    if m_inline_del:
        d_node = DelayNode(line=ln, delay_expr=m_inline_del.group(1).strip("() "))
        trailing = _parse_single_stmt(ln, m_inline_del.group(2).strip())
        if trailing:
            return SeqNode(line=ln, stmts=[d_node, trailing])
        return d_node

    # Compound assignment (+=, -=) or increment/decrement (x++; ++x;)
    m_comp_asgn = re.match(r'^([a-zA-Z_]\w*)\s*(\+=|-=)\s*(.+?)\s*;$', s)
    if m_comp_asgn:
        lhs, op, rhs = m_comp_asgn.group(1), m_comp_asgn.group(2), m_comp_asgn.group(3)
        return AssignNode(line=ln, lhs=lhs, rhs=f"{lhs} {op[0]} ({rhs})")

    m_inc_stmt = re.match(r'^(?:\+\+|--)?([a-zA-Z_]\w*)(?:\+\+|--)?\s*;$', s)
    if m_inc_stmt and ("++" in s or "--" in s):
        v = m_inc_stmt.group(1)
        op = "+" if "++" in s else "-"
        return AssignNode(line=ln, lhs=v, rhs=f"{v} {op} 1")

    # Assignment with RHS call (e.g. pkt = my_pkt::type_id::create("pkt", this);)
    m_asgn = RE_ASSIGN.match(s)
    if m_asgn:
        lhs, rhs = m_asgn.group(1), m_asgn.group(2).strip()
        if "type_id::create" in rhs or "new(" in rhs or ".get(" in rhs:
            return AssignNode(line=ln, lhs=lhs, rhs=rhs)
        return AssignNode(line=ln, lhs=lhs, rhs=rhs)

    m_call = RE_CALL.match(s)
    if m_call:
        obj = (m_call.group(1) or "").strip()
        method = m_call.group(2).strip()
        args = m_call.group(3).strip()
        return CallNode(line=ln, obj=obj, method=method, args=args)

    return None


def _parse_block(chunks: List[Tuple[int, str]], idx: int, stop_words: Tuple[str, ...]) -> Tuple[List[Stmt], int]:
    stmts: List[Stmt] = []
    n = len(chunks)

    while idx < n:
        ln, txt = chunks[idx]
        low = txt.split()[0] if txt.split() else ""
        if any(txt == sw or txt.startswith(sw + " ") or txt.startswith(sw + ";") or txt.startswith(sw + ":") for sw in stop_words):
            return stmts, idx

        if txt == "begin" or txt.startswith("begin ") or txt.startswith("begin:"):
            sub, idx = _parse_block(chunks, idx + 1, ("end",))
            stmts.extend(sub)
            if idx < n and (chunks[idx][1] == "end" or chunks[idx][1].startswith("end")):
                idx += 1
            continue

        if txt == "fork" or txt.startswith("fork ") or txt.startswith("fork:"):
            branches: List[List[Stmt]] = []
            idx += 1
            join_kind = "join"
            while idx < n:
                bln, btxt = chunks[idx]
                if btxt.startswith(("join_any", "join_none", "join")):
                    join_kind = btxt.split()[0].rstrip(";")
                    idx += 1
                    break
                if btxt == "begin" or btxt.startswith("begin ") or btxt.startswith("begin:"):
                    b_stmts, idx = _parse_block(chunks, idx + 1, ("end",))
                    branches.append(b_stmts)
                    if idx < n and chunks[idx][1].startswith("end"):
                        idx += 1
                else:
                    st = _parse_single_stmt(bln, btxt)
                    if st:
                        branches.append([st])
                    idx += 1
            stmts.append(ForkNode(line=ln, join_kind=join_kind, branches=branches))
            continue

        m_if = re.match(r'^if\s*\((.*)\)\s*(begin\b.*)?$', txt, re.S)
        if m_if or re.match(r'^if\s*\(', txt):
            # Extract condition and optional inline statement
            m_inline = re.match(r'^if\s*\((.+?)\)\s*(.+)$', txt, re.S)
            cond = ""
            rest = ""
            if m_inline:
                # Balance parens to split cond and rest
                p = 0
                split_pos = -1
                for k, ch in enumerate(txt):
                    if ch == "(":
                        p += 1
                    elif ch == ")":
                        p -= 1
                        if p == 0:
                            split_pos = k
                            break
                if split_pos != -1:
                    first_open = txt.find("(")
                    cond = txt[first_open + 1:split_pos].strip()
                    rest = txt[split_pos + 1:].strip()

            then_body: List[Stmt] = []
            else_body: List[Stmt] = []
            idx += 1

            if rest and not rest.startswith("begin"):
                st = _parse_single_stmt(ln, rest)
                if st:
                    then_body.append(st)
            elif rest.startswith("begin"):
                then_body, idx = _parse_block(chunks, idx, ("end",))
                if idx < n and chunks[idx][1].startswith("end"):
                    idx += 1
            elif idx < n:
                if chunks[idx][1].startswith("begin"):
                    then_body, idx = _parse_block(chunks, idx + 1, ("end",))
                    if idx < n and chunks[idx][1].startswith("end"):
                        idx += 1
                else:
                    st = _parse_single_stmt(chunks[idx][0], chunks[idx][1])
                    if st:
                        then_body.append(st)
                    idx += 1

            # Optional else
            if idx < n and (chunks[idx][1] == "else" or chunks[idx][1].startswith("else ")):
                e_ln, e_txt = chunks[idx]
                e_rest = e_txt[4:].strip()
                idx += 1
                if e_rest and not e_rest.startswith("begin"):
                    if e_rest.startswith("if"):
                        # Recurse on else if by pushing synthetic chunk
                        chunks.insert(idx, (e_ln, e_rest))
                        sub_e, idx = _parse_block(chunks, idx, stop_words)
                        # Only consume one statement
                        if sub_e:
                            else_body.append(sub_e[0])
                    else:
                        st = _parse_single_stmt(e_ln, e_rest)
                        if st:
                            else_body.append(st)
                elif e_rest.startswith("begin"):
                    else_body, idx = _parse_block(chunks, idx, ("end",))
                    if idx < n and chunks[idx][1].startswith("end"):
                        idx += 1
                elif idx < n:
                    if chunks[idx][1].startswith("begin"):
                        else_body, idx = _parse_block(chunks, idx + 1, ("end",))
                        if idx < n and chunks[idx][1].startswith("end"):
                            idx += 1
                    else:
                        st = _parse_single_stmt(chunks[idx][0], chunks[idx][1])
                        if st:
                            else_body.append(st)
                        idx += 1

            stmts.append(IfNode(line=ln, cond=cond, then_body=then_body, else_body=else_body))
            continue

        m_loop = re.match(r'^(for|repeat|foreach|while)\s*\((.+)\)\s*(begin\b.*)?$', txt, re.S)
        if m_loop:
            kind = m_loop.group(1)
            p = 0
            split_pos = -1
            for k, ch in enumerate(txt):
                if ch == "(":
                    p += 1
                elif ch == ")":
                    p -= 1
                    if p == 0:
                        split_pos = k
                        break
            first_open = txt.find("(")
            header = txt[first_open + 1:split_pos].strip() if split_pos != -1 else m_loop.group(2)
            rest = txt[split_pos + 1:].strip() if split_pos != -1 else ""
            body: List[Stmt] = []
            idx += 1
            if rest and not rest.startswith("begin"):
                st = _parse_single_stmt(ln, rest)
                if st:
                    body.append(st)
            elif rest.startswith("begin"):
                body, idx = _parse_block(chunks, idx, ("end",))
                if idx < n and chunks[idx][1].startswith("end"):
                    idx += 1
            elif idx < n:
                if chunks[idx][1].startswith("begin"):
                    body, idx = _parse_block(chunks, idx + 1, ("end",))
                    if idx < n and chunks[idx][1].startswith("end"):
                        idx += 1
                else:
                    st = _parse_single_stmt(chunks[idx][0], chunks[idx][1])
                    if st:
                        body.append(st)
                    idx += 1
            stmts.append(LoopNode(line=ln, kind=kind, header=header, body=body))
            continue

        st = _parse_single_stmt(ln, txt)
        if st:
            stmts.append(st)
        idx += 1

    return stmts, idx


def parse_sv_suite(files_data: List[Dict[str, Any]]) -> Tuple[Dict[str, ClassDef], List[Tuple[str, int, List[Stmt]]], Dict[str, str]]:
    """Parse all .sv/.svh files in a suite into ClassDefs, top-level initial blocks, and module var types."""
    classes: Dict[str, ClassDef] = {}
    initials: List[Tuple[str, int, List[Stmt]]] = []
    module_vars: Dict[str, str] = {}

    sv_files = [fd for fd in files_data if fd["name"].endswith((".sv", ".svh"))]
    for fd in sv_files:
        fname = fd["name"]
        lines = _strip_comments_preserve_lines(fd["raw_content"])
        chunks = _tokenize_statements(lines)
        n = len(chunks)
        idx = 0
        cur_class: Optional[ClassDef] = None

        while idx < n:
            ln, txt = chunks[idx]

            m_cls = re.match(r'^(virtual\s+)?class\s+([a-zA-Z_]\w*)(?:\s*#\([^)]*\))?(?:\s+extends\s+([a-zA-Z_]\w*))?', txt)
            if m_cls:
                cname = m_cls.group(2)
                cbase = m_cls.group(3) or "uvm_object"
                cur_class = ClassDef(
                    name=cname,
                    base=cbase,
                    file=fname,
                    line=ln,
                    is_virtual=bool(m_cls.group(1)),
                )
                classes[cname] = cur_class
                idx += 1
                continue

            if txt.startswith("endclass"):
                cur_class = None
                idx += 1
                continue

            m_fn = re.match(r'^(?:virtual\s+|static\s+|protected\s+|local\s+)*(function|task)\s+(?:automatic\s+)?(?:[\w:]+\s+)?([a-zA-Z_]\w*)\s*\(([^)]*)\)', txt)
            if m_fn and cur_class is not None:
                is_task = m_fn.group(1) == "task"
                mname = m_fn.group(2)
                raw_params = m_fn.group(3).strip()
                params: List[str] = []
                if raw_params:
                    for p in _split_top_level_args(raw_params):
                        p_clean = p.split("=")[0].strip()
                        tokens = re.findall(r'[a-zA-Z_]\w*', p_clean)
                        if tokens:
                            params.append(tokens[-1])
                stop_kw = ("endtask",) if is_task else ("endfunction",)
                body, idx = _parse_block(chunks, idx + 1, stop_kw)
                if idx < n and chunks[idx][1].startswith(stop_kw):
                    idx += 1
                cur_class.methods[mname] = MethodDef(name=mname, is_task=is_task, line=ln, params=params, body=body)
                continue

            if txt == "initial" or txt.startswith("initial "):
                rest = txt[7:].strip()
                if rest.startswith("begin"):
                    after_begin = rest[5:].strip()
                    if after_begin:
                        chunks.insert(idx + 1, (ln, after_begin))
                    body, idx = _parse_block(chunks, idx + 1, ("end",))
                    if idx < n and chunks[idx][1].startswith("end"):
                        idx += 1
                else:
                    body, idx = _parse_block(chunks, idx + 1, ("endmodule", "endprogram", "initial"))
                initials.append((fname, ln, body))
                continue

            if cur_class is not None:
                m_prop = re.match(r'^(?:int|string|bit|logic|time)\s+([a-zA-Z_]\w*)\s*=\s*([^;]+);', txt)
                if m_prop:
                    cur_class.props[m_prop.group(1)] = m_prop.group(2).strip()
                m_cprop = re.match(r'^([a-zA-Z_]\w*)(?:\s*#\([^)]*\))?\s+([a-zA-Z_]\w*)\s*;', txt)
                if m_cprop and m_cprop.group(1) not in ("int", "string", "bit", "logic", "time", "rand", "local", "protected"):
                    cur_class.props[f"__type__{m_cprop.group(2)}"] = m_cprop.group(1)
            else:
                m_mvar = re.match(r'^([a-zA-Z_]\w*)\s+([a-zA-Z_]\w*)\s*;', txt)
                if m_mvar:
                    module_vars[m_mvar.group(2)] = m_mvar.group(1)

            idx += 1

    return classes, initials, module_vars


# ---------------------------------------------------------------------------
# Symbolic Simulation Engine
# ---------------------------------------------------------------------------

@dataclass
class ComponentInst:
    inst_name: str
    full_path: str
    class_name: str
    parent: Optional["ComponentInst"] = None
    children: List["ComponentInst"] = field(default_factory=list)


BUILTIN_UVM_PARENTS = {
    "uvm_test": "uvm_component",
    "uvm_env": "uvm_component",
    "uvm_agent": "uvm_component",
    "uvm_driver": "uvm_component",
    "uvm_monitor": "uvm_component",
    "uvm_sequencer": "uvm_component",
    "uvm_scoreboard": "uvm_component",
    "uvm_subscriber": "uvm_component",
    "uvm_reg_predictor": "uvm_component",
    "uvm_reg_sequence": "uvm_sequence",
    "uvm_reg_frontdoor": "uvm_sequence",
    "uvm_sequence": "uvm_sequence_item",
    "uvm_sequence_item": "uvm_transaction",
    "uvm_transaction": "uvm_object",
    "uvm_callback": "uvm_object",
}


class SimEngine:
    def __init__(self, classes: Dict[str, ClassDef], initials: List[Tuple[str, int, List[Stmt]]], module_vars: Dict[str, str], files_data: List[Dict[str, Any]], meta: Dict[str, Any]):
        self.classes = classes
        self.initials = initials
        self.module_vars = module_vars
        self.files_data = files_data
        self.meta = meta

        self.events: List[Dict[str, Any]] = []
        self.seen_event_cap = 120
        self.sim_time = 0
        self.seq_counter = 0

        self.config_db: Dict[str, Any] = {}
        self.type_overrides: Dict[str, str] = {}
        self.static_counters: Dict[str, int] = {}
        self.rng = random.Random(42)
        self.objections = 0
        self.drain_time = 0
        self.pq: List[Tuple[int, int, Any]] = []
        self.fifos: Dict[str, Dict[str, Any]] = {}
        self.root_test_name = self._resolve_root_test_name()

        self.root_comp: Optional[ComponentInst] = None
        self.topo_names = [t.get("name", "") for t in meta.get("topology", []) if t.get("name")]

    def _is_subclass(self, cls_name: str, ancestor: str) -> bool:
        cur = cls_name
        visited = set()
        while cur and cur not in visited:
            if cur == ancestor:
                return True
            visited.add(cur)
            if cur in BUILTIN_UVM_PARENTS:
                cur = BUILTIN_UVM_PARENTS[cur]
                continue
            cdef = self.classes.get(cur)
            cur = cdef.base if cdef else ""
        return False

    def _resolve_root_test_name(self) -> str:
        # 1. Check Makefiles for +UVM_TESTNAME=
        for fd in self.files_data:
            if "Makefile" in fd["name"]:
                m = re.search(r'\+UVM_TESTNAME=([a-zA-Z_]\w*)', fd["raw_content"])
                if m and m.group(1) in self.classes:
                    return m.group(1)

        # 2. Check run_test("...") in initial blocks
        for _, _, body in self.initials:
            for st in body:
                if isinstance(st, CallNode) and st.method == "run_test":
                    m_q = re.match(r'^"([^"]+)"$', st.args.strip())
                    if m_q and m_q.group(1) in self.classes:
                        return m_q.group(1)

        # 3. First concrete uvm_test subclass
        for cname, cdef in self.classes.items():
            if not cdef.is_virtual and self._is_subclass(cname, "uvm_test"):
                return cname

        # 4. Component instantiated directly in initial block (e.g. `mytop = new("top");`)
        for _, _, body in self.initials:
            for st in body:
                if isinstance(st, AssignNode) and "new(" in st.rhs and st.lhs in self.module_vars:
                    cls_cand = self.module_vars[st.lhs]
                    if cls_cand in self.classes and self._is_subclass(cls_cand, "uvm_component"):
                        return cls_cand

        # 5. Fallback to first concrete uvm_env or uvm_component
        for base in ("uvm_env", "uvm_component"):
            for cname, cdef in self.classes.items():
                if not cdef.is_virtual and self._is_subclass(cname, base):
                    return cname

        return ""

    def _find_method_chain(self, class_name: str, method_name: str) -> List[Tuple[ClassDef, MethodDef]]:
        """Return [most_derived, ..., base] implementations of method_name."""
        chain: List[Tuple[ClassDef, MethodDef]] = []
        cur = class_name
        visited = set()
        while cur and cur not in visited:
            visited.add(cur)
            cdef = self.classes.get(cur)
            if not cdef:
                break
            if method_name in cdef.methods:
                chain.append((cdef, cdef.methods[method_name]))
            cur = cdef.base
        return chain

    def _safe_int_eval(self, expr: str) -> Optional[int]:
        """Safely evaluate a pure integer arithmetic expression using ast."""
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError:
            return None

        def _eval_node(node):
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
                return node.value
            if isinstance(node, ast.UnaryOp):
                v = _eval_node(node.operand)
                if v is None:
                    return None
                if isinstance(node.op, ast.UAdd):
                    return +v
                if isinstance(node.op, ast.USub):
                    return -v
                return None
            if isinstance(node, ast.BinOp):
                l = _eval_node(node.left)
                r = _eval_node(node.right)
                if l is None or r is None:
                    return None
                if isinstance(node.op, ast.Add):
                    return l + r
                if isinstance(node.op, ast.Sub):
                    return l - r
                if isinstance(node.op, ast.Mult):
                    return l * r
                if isinstance(node.op, ast.FloorDiv) or isinstance(node.op, ast.Div):
                    return l // r if r != 0 else 0
                if isinstance(node.op, ast.Mod):
                    return l % r if r != 0 else 0
                if isinstance(node.op, ast.LShift):
                    return l << min(r, 31)
                if isinstance(node.op, ast.RShift):
                    return l >> min(r, 31)
                if isinstance(node.op, ast.BitAnd):
                    return l & r
                if isinstance(node.op, ast.BitOr):
                    return l | r
            return None

        return _eval_node(tree)

    def _eval_expr(self, expr: str, env: Dict[str, Any], inst: Optional[ComponentInst], cdef: Optional[ClassDef]) -> Any:
        e = expr.strip()
        if not e:
            return ""
        m_q = re.match(r'^"([^"]*)"$', e)
        if m_q:
            return m_q.group(1)
        if re.match(r'^-?\d+$', e):
            return int(e)
        m_time_lit = re.match(r'^(\d+)\s*(fs|ps|ns|us|ms|s)$', e, re.I)
        if m_time_lit:
            num = int(m_time_lit.group(1))
            unit = m_time_lit.group(2).lower()
            mult = {"fs": 1, "ps": 1, "ns": 1, "us": 1000, "ms": 1000000, "s": 1000000000}.get(unit, 1)
            return num * mult
        # SystemVerilog hex/dec literals like 32'hFF, 8'd10, 'h1a
        m_lit = re.match(r"^(?:\d+)?'([hdbo])([0-9a-fA-F_]+)$", e, re.I)
        if m_lit:
            base = {"h": 16, "d": 10, "b": 2, "o": 8}[m_lit.group(1).lower()]
            return int(m_lit.group(2).replace("_", ""), base)
        if e in env:
            return env[e]
        if e in ("$time", "$stime", "$realtime"):
            return self.sim_time
        if e in ("$urandom", "$urandom()", "$random", "$random()"):
            return self.rng.randint(1, 255)
        m_ur = re.match(r'^\$urandom_range\s*\(([^)]+)\)$', e)
        if m_ur:
            parts = _split_top_level_args(m_ur.group(1))
            nums = [self._eval_expr(p, env, inst, cdef) for p in parts]
            if len(nums) == 2 and isinstance(nums[0], int) and isinstance(nums[1], int):
                lo, hi = min(nums[0], nums[1]), max(nums[0], nums[1])
                return self.rng.randint(lo, hi)
            if len(nums) == 1 and isinstance(nums[0], int) and nums[0] >= 0:
                return self.rng.randint(0, nums[0])
            return self.rng.randint(0, 100)
        if e in ("get_type_name()", "this.get_type_name()"):
            return cdef.name if cdef else "uvm_object"
        if e in ("get_full_name()", "this.get_full_name()"):
            return inst.full_path if inst else "uvm_test_top"
        if e in ("get_name()", "this.get_name()"):
            return inst.inst_name if inst else "uvm_test_top"
        m_obj_get = re.match(r'^([a-zA-Z_]\w*)\.(get_name|get_full_name|get_type_name|get_realtime|get_objection_total|sprint|convert2string)\s*(?:\([^)]*\))?$', e)
        if m_obj_get:
            obj_name, m_name = m_obj_get.group(1), m_obj_get.group(2)
            if m_name == "get_name":
                return env.get(f"__obj_name__{obj_name}", obj_name)
            if m_name == "get_full_name":
                if obj_name in ("source_obj", "this"):
                    return inst.full_path if inst else "uvm_test_top"
                base = inst.full_path if inst else "uvm_test_top"
                sub = env.get(f"__obj_name__{obj_name}", obj_name)
                return f"{base}.{sub}"
            if m_name == "get_type_name":
                return cdef.props.get(f"__type__{obj_name}", obj_name) if cdef else obj_name
            if m_name == "get_realtime":
                return self.sim_time
            if m_name == "get_objection_total":
                return self.objections
            if m_name == "sprint":
                return "<topology>" if obj_name == "this" else f"<{obj_name}>"
            if m_name == "convert2string":
                return f"<{obj_name}>"

        # $sformatf("fmt", a, b, ...) or $psprintf("fmt", a, b, ...)
        m_sf = re.match(r'^\$(?:sformatf|psprintf)\s*\((.*)\)$', e, re.S)
        if m_sf:
            parts = _split_top_level_args(m_sf.group(1))
            if parts:
                fmt = str(self._eval_expr(parts[0], env, inst, cdef))
                vals = [self._eval_expr(p, env, inst, cdef) for p in parts[1:]]
                idx = 0

                def _repl(m):
                    nonlocal idx
                    spec = m.group(0)
                    if spec == "%%":
                        return "%"
                    if spec.endswith("m"):
                        return inst.full_path if inst else (cdef.name if cdef else "top")
                    if idx < len(vals):
                        v = vals[idx]
                        idx += 1
                        if spec.endswith(("x", "X")) and isinstance(v, int):
                            return format(v, "x")
                        if spec.endswith("b") and isinstance(v, int):
                            return format(v, "b")
                        return str(v)
                    return "<val>"

                return re.sub(r'%%|%(?:[-+#0 ]*\d*(?:\.\d+)?)?[dxhobsfgtmpuvzec]', _repl, fmt, flags=re.I)

        # String concatenation {a, b, c}
        if e.startswith("{") and e.endswith("}"):
            parts = _split_top_level_args(e[1:-1])
            return "".join(str(self._eval_expr(p, env, inst, cdef)) for p in parts)

        # General integer arithmetic with env variables & $time / $urandom substitution
        expr_sub = re.sub(r'\$(?:time|stime|realtime)\b', str(self.sim_time), e)
        expr_sub = re.sub(r'\$(?:urandom|random)(?:\(\))?', lambda _: str(self.rng.randint(1, 255)), expr_sub)
        for k, v in env.items():
            if isinstance(v, int):
                expr_sub = re.sub(rf'\b{re.escape(k)}\b', str(v), expr_sub)
        if re.match(r'^[\d\s+\-*/%()<>|&]+$', expr_sub):
            calc = self._safe_int_eval(expr_sub.replace("/", "//"))
            if calc is not None:
                return calc

        return re.sub(r'"([^"]*)"', r'\1', e)[:90]

    def _emit_event(self, kind: str, severity: str, file: str, line: int, scope: str, method: str, tag: str, msg: str, inst_path: str = "", time_ns: Optional[int] = None):
        if len(self.events) >= self.seen_event_cap:
            return
        t_ns = self.sim_time if time_ns is None else time_ns
        clean_msg = msg.replace("\\n", " ").strip()
        clean_msg = re.sub(r'\s+', ' ', clean_msg)
        matched_topo = [t for t in self.topo_names if t.lower() in scope.lower() or scope.lower() in t.lower()]
        component = ", ".join(matched_topo[:2]) if matched_topo else (inst_path or scope)
        self.events.append({
            "kind": kind,
            "severity": severity,
            "file": file,
            "line": line,
            "scope": inst_path or scope,
            "method": method,
            "tag": re.sub(r'[^A-Za-z0-9_]', '', tag)[:18] or "INFO",
            "msg": clean_msg,
            "time_ns": t_ns,
            "component": component,
            "order": 50,
        })

    def _body_only_errors(self, stmts: List[Stmt]) -> bool:
        if not stmts:
            return False
        return all(isinstance(s, ReportNode) and s.severity in ("UVM_ERROR", "UVM_FATAL") for s in stmts)

    def _eval_condition(self, cond: str, env: Dict[str, Any], then_body: List[Stmt]) -> bool:
        c = cond.strip()
        # Negative config_db::get check -> nominal path succeeds (returns True, so !get is False)
        if ("uvm_config_db" in c or "get_config_" in c) and (c.startswith("!") or "== 0" in c):
            return False
        if "uvm_config_db" in c or "get_config_" in c:
            return True
        # Guard that only emits UVM_ERROR / UVM_FATAL -> skip on nominal path
        if self._body_only_errors(then_body):
            return False
        # Simple variable comparison (e.g. i == 0, count > 0)
        m_cmp = re.match(r'^([a-zA-Z_]\w*)\s*(==|!=|<|>|<=|>=)\s*(\d+)$', c)
        if m_cmp and m_cmp.group(1) in env and isinstance(env[m_cmp.group(1)], int):
            lv = env[m_cmp.group(1)]
            rv = int(m_cmp.group(3))
            op = m_cmp.group(2)
            if op == "==":
                return lv == rv
            if op == "!=":
                return lv != rv
            if op == "<":
                return lv < rv
            if op == ">":
                return lv > rv
            if op == "<=":
                return lv <= rv
            if op == ">=":
                return lv >= rv
        return True

    def _loop_iterations(self, node: LoopNode, env: Dict[str, Any], inst: Optional[ComponentInst], cdef: Optional[ClassDef]) -> List[Tuple[str, Any]]:
        hdr = node.header.strip()
        if node.kind == "repeat":
            val = self._eval_expr(hdr, env, inst, cdef)
            cnt = val if isinstance(val, int) and val > 0 else 2
            return [("", i) for i in range(min(cnt, 4))]
        if node.kind == "for":
            m = re.match(r'(?:int\s+)?([a-zA-Z_]\w*)\s*=\s*(\d+)\s*;\s*\1\s*<\s*([^;]+);', hdr)
            if m:
                vname = m.group(1)
                start_v = int(m.group(2))
                lim = self._eval_expr(m.group(3), env, inst, cdef)
                end_v = lim if isinstance(lim, int) and lim > start_v else start_v + 3
                return [(vname, i) for i in range(start_v, min(end_v, start_v + 4))]
        return [("", 0), ("", 1)]

    def _exec_stmts_sync(self, stmts: List[Stmt], cdef: Optional[ClassDef], method_name: str, inst: Optional[ComponentInst], env: Dict[str, Any], file_override: str = ""):
        fname = file_override or (cdef.file if cdef else "")
        scope = cdef.name if cdef else (inst.class_name if inst else "tb_top")
        inst_path = inst.full_path if inst else scope

        for st in stmts:
            if len(self.events) >= self.seen_event_cap:
                return

            if isinstance(st, AssignNode):
                rhs = st.rhs
                # Handle post-increment like `s_inst++`
                m_inc = re.match(r'^([a-zA-Z_]\w*)\+\+$', rhs)
                if m_inc:
                    vname = m_inc.group(1)
                    key = f"{cdef.name if cdef else ''}::{vname}"
                    cur_val = self.static_counters.get(key, 0)
                    self.static_counters[key] = cur_val + 1
                    env[st.lhs] = cur_val
                    continue
                # Component creation via factory or new()
                m_cr = re.search(r'([a-zA-Z_]\w*)::type_id::create\s*\(\s*"([^"]+)"', rhs)
                if m_cr and inst is not None:
                    req_cls = m_cr.group(1)
                    child_name = m_cr.group(2)
                    real_cls = self.type_overrides.get(req_cls, req_cls)
                    if self._is_subclass(real_cls, "uvm_component") or real_cls in self.classes:
                        if self._is_subclass(real_cls, "uvm_component"):
                            child = ComponentInst(
                                inst_name=child_name,
                                full_path=f"{inst.full_path}.{child_name}",
                                class_name=real_cls,
                                parent=inst,
                            )
                            inst.children.append(child)
                        env[st.lhs] = child_name
                    continue
                m_new = re.match(r'^new\s*\(\s*"([^"]+)"\s*,\s*this\s*\)', rhs)
                if m_new and inst is not None and cdef is not None:
                    child_name = m_new.group(1)
                    decl_cls = cdef.props.get(f"__type__{st.lhs}", "")
                    if decl_cls and self._is_subclass(decl_cls, "uvm_component"):
                        child = ComponentInst(
                            inst_name=child_name,
                            full_path=f"{inst.full_path}.{child_name}",
                            class_name=decl_cls,
                            parent=inst,
                        )
                        inst.children.append(child)
                        env[st.lhs] = child_name
                        continue
                env[st.lhs] = self._eval_expr(rhs, env, inst, cdef)

            elif isinstance(st, ReportNode):
                tag = str(self._eval_expr(st.tag_expr, env, inst, cdef))
                msg = str(self._eval_expr(st.msg_expr, env, inst, cdef))
                self._emit_event(
                    kind="display" if st.is_display else "log",
                    severity=st.severity,
                    file=fname,
                    line=st.line,
                    scope=scope,
                    method=method_name,
                    tag=tag,
                    msg=msg,
                    inst_path=inst_path,
                )

            elif isinstance(st, CallNode):
                if st.obj == "super" and cdef is not None:
                    chain = self._find_method_chain(cdef.base, st.method)
                    if chain:
                        base_cdef, base_m = chain[0]
                        self._exec_stmts_sync(base_m.body, base_cdef, st.method, inst, env)
                elif st.method in ("set_type_override_by_type", "set_type_override"):
                    args = _split_top_level_args(st.args)
                    if len(args) >= 2:
                        orig = args[0].split("::")[0].strip().strip('"')
                        over = args[1].split("::")[0].strip().strip('"')
                        self.type_overrides[orig] = over
                elif "uvm_config" in st.obj and st.method == "set":
                    args = _split_top_level_args(st.args)
                    if len(args) >= 4:
                        key = str(self._eval_expr(args[2], env, inst, cdef))
                        val = self._eval_expr(args[3], env, inst, cdef)
                        self.config_db[key] = val
                elif st.method == "run_test":
                    m_q = re.match(r'^"([^"]+)"$', st.args.strip())
                    if m_q and m_q.group(1) in self.classes:
                        self.root_test_name = m_q.group(1)
                    self._emit_event(
                        kind="run_test",
                        severity="UVM_INFO",
                        file=fname,
                        line=st.line,
                        scope=scope,
                        method="initial",
                        tag="RNTST",
                        msg=f"Running test {self.root_test_name or 'uvm_test_top'}...",
                        inst_path="reporter",
                    )
                elif cdef is not None and st.method in cdef.methods and not st.obj:
                    sub_m = cdef.methods[st.method]
                    self._exec_stmts_sync(sub_m.body, cdef, st.method, inst, dict(env))
                elif st.obj and st.obj in self.module_vars:
                    t_cls = self.module_vars[st.obj]
                    if t_cls in self.classes and st.method in self.classes[t_cls].methods:
                        tcdef = self.classes[t_cls]
                        sub_m = tcdef.methods[st.method]
                        self._exec_stmts_sync(sub_m.body, tcdef, st.method, inst, dict(tcdef.props))

            elif isinstance(st, IfNode):
                if self._eval_condition(st.cond, env, st.then_body):
                    self._exec_stmts_sync(st.then_body, cdef, method_name, inst, env, file_override=fname)
                elif st.else_body:
                    self._exec_stmts_sync(st.else_body, cdef, method_name, inst, env, file_override=fname)

            elif isinstance(st, LoopNode):
                for vname, val in self._loop_iterations(st, env, inst, cdef):
                    if vname:
                        env[vname] = val
                    self._exec_stmts_sync(st.body, cdef, method_name, inst, env, file_override=fname)

    def _instantiate_from_new(self, comp: ComponentInst):
        """Inspect constructor `new` (if present) for child component instantiations."""
        cdef = self.classes.get(comp.class_name)
        if not cdef or "new" not in cdef.methods:
            return
        env = dict(cdef.props)
        for st in cdef.methods["new"].body:
            if isinstance(st, AssignNode):
                m_new = re.match(r'^new\s*\(\s*"([^"]+)"\s*,\s*this\s*\)', st.rhs)
                if m_new:
                    child_name = m_new.group(1)
                    decl_cls = cdef.props.get(f"__type__{st.lhs}", "")
                    if decl_cls and self._is_subclass(decl_cls, "uvm_component"):
                        if not any(c.inst_name == child_name for c in comp.children):
                            child = ComponentInst(
                                inst_name=child_name,
                                full_path=f"{comp.full_path}.{child_name}",
                                class_name=decl_cls,
                                parent=comp,
                            )
                            comp.children.append(child)
                            self._instantiate_from_new(child)

    def _run_phase_recursive_topdown(self, comp: ComponentInst, phase_names: Tuple[str, ...]):
        self._instantiate_from_new(comp)
        cdef = self.classes.get(comp.class_name)
        if cdef:
            for pname in phase_names:
                chain = self._find_method_chain(comp.class_name, pname)
                if chain:
                    m_cdef, m_def = chain[0]
                    self._emit_event(
                        kind="phase",
                        severity="UVM_INFO",
                        file=m_cdef.file,
                        line=m_def.line,
                        scope=m_cdef.name,
                        method=pname,
                        tag="PH_TRACE",
                        msg=f"Executing {comp.full_path}::{pname}()",
                        inst_path=comp.full_path,
                    )
                    env = dict(m_cdef.props)
                    self._exec_stmts_sync(m_def.body, m_cdef, pname, comp, env)
                    break
        for ch in comp.children:
            self._run_phase_recursive_topdown(ch, phase_names)

    def _run_phase_recursive_bottomup(self, comp: ComponentInst, phase_names: Tuple[str, ...]):
        for ch in comp.children:
            self._run_phase_recursive_bottomup(ch, phase_names)
        cdef = self.classes.get(comp.class_name)
        if cdef:
            for pname in phase_names:
                chain = self._find_method_chain(comp.class_name, pname)
                if chain:
                    m_cdef, m_def = chain[0]
                    self._emit_event(
                        kind="phase",
                        severity="UVM_INFO",
                        file=m_cdef.file,
                        line=m_def.line,
                        scope=m_cdef.name,
                        method=pname,
                        tag="PH_TRACE",
                        msg=f"Executing {comp.full_path}::{pname}()",
                        inst_path=comp.full_path,
                    )
                    env = dict(m_cdef.props)
                    self._exec_stmts_sync(m_def.body, m_cdef, pname, comp, env)
                    break

    def _collect_run_tasks(self, comp: ComponentInst, out: List[Tuple[ComponentInst, ClassDef, MethodDef]]):
        for pname in ("run_phase", "run", "main_phase", "reset_phase", "configure_phase"):
            chain = self._find_method_chain(comp.class_name, pname)
            if chain:
                m_cdef, m_def = chain[0]
                out.append((comp, m_cdef, m_def))
                break
        for ch in comp.children:
            self._collect_run_tasks(ch, out)

    def _get_fifo(self, key: str = "default") -> Dict[str, Any]:
        if key not in self.fifos:
            self.fifos[key] = {
                "items": [],
                "max_size": 1,
                "wait_get": [],
                "wait_put": [],
            }
        return self.fifos[key]

    def _schedule_task(self, wake_time: int, gen: Any):
        self.seq_counter += 1
        heapq.heappush(self.pq, (wake_time, self.seq_counter, gen))

    def _wake_fifo_waiters(self, fifo: Dict[str, Any], wait_key: str):
        waiters = fifo[wait_key]
        if waiters:
            gen = waiters.pop(0)
            self._schedule_task(self.sim_time, gen)

    def _make_task_gen(self, stmts: List[Stmt], cdef: ClassDef, method_name: str, inst: ComponentInst, env: Dict[str, Any], on_done=None):
        """Generator yielding control tokens: ('delay', ns) | ('wait_fifo_get', fifo) | ('wait_fifo_put', fifo) | ('wait_fork', state)."""
        try:
            for st in stmts:
                if len(self.events) >= self.seen_event_cap:
                    return

                if isinstance(st, SeqNode):
                    yield from self._make_task_gen(st.stmts, cdef, method_name, inst, env)

                elif isinstance(st, DelayNode):
                    val = self._eval_expr(st.delay_expr, env, inst, cdef)
                    delay = val if isinstance(val, int) and val > 0 else 10
                    yield ("delay", delay)

                elif isinstance(st, AssignNode):
                    m_inc = re.match(r'^([a-zA-Z_]\w*)\+\+$', st.rhs)
                    if m_inc:
                        vname = m_inc.group(1)
                        key = f"{cdef.name}::{vname}"
                        cur_val = self.static_counters.get(key, 0)
                        self.static_counters[key] = cur_val + 1
                        env[st.lhs] = cur_val
                    else:
                        env[st.lhs] = self._eval_expr(st.rhs, env, inst, cdef)

                elif isinstance(st, ReportNode):
                    tag = str(self._eval_expr(st.tag_expr, env, inst, cdef))
                    msg = str(self._eval_expr(st.msg_expr, env, inst, cdef))
                    self._emit_event(
                        kind="display" if st.is_display else "log",
                        severity=st.severity,
                        file=cdef.file,
                        line=st.line,
                        scope=cdef.name,
                        method=method_name,
                        tag=tag,
                        msg=msg,
                        inst_path=inst.full_path,
                    )

                elif isinstance(st, CallNode):
                    if st.method == "raise_objection":
                        self.objections += 1
                        self._emit_event(
                            kind="objection",
                            severity="UVM_INFO",
                            file=cdef.file,
                            line=st.line,
                            scope=cdef.name,
                            method=method_name,
                            tag="OBJTN",
                            msg=f"{inst.full_path} raised objection (total={self.objections})",
                            inst_path=inst.full_path,
                        )
                    elif st.method == "drop_objection":
                        self.objections = max(0, self.objections - 1)
                        self._emit_event(
                            kind="objection",
                            severity="UVM_INFO",
                            file=cdef.file,
                            line=st.line,
                            scope=cdef.name,
                            method=method_name,
                            tag="OBJTN",
                            msg=f"{inst.full_path} dropped objection (total={self.objections})",
                            inst_path=inst.full_path,
                        )
                        if "dropped" in cdef.methods:
                            cb = cdef.methods["dropped"]
                            cb_env = dict(env)
                            cb_env.update({"count": 1, "source_obj": inst.full_path})
                            self._exec_stmts_sync(cb.body, cdef, "dropped", inst, cb_env)
                    elif st.method == "set_drain_time":
                        args = _split_top_level_args(st.args)
                        if args:
                            val = self._eval_expr(args[-1], env, inst, cdef)
                            if isinstance(val, int):
                                self.drain_time = val
                    elif st.method in ("put", "try_put"):
                        fifo = self._get_fifo("default")
                        if st.method == "put" and len(fifo["items"]) >= fifo["max_size"]:
                            yield ("wait_fifo_put", fifo)
                        if len(fifo["items"]) < fifo["max_size"]:
                            val = self._eval_expr(st.args, env, inst, cdef) if st.args else "pkt"
                            fifo["items"].append(val)
                            self._wake_fifo_waiters(fifo, "wait_get")
                    elif st.method in ("get", "peek", "try_get"):
                        fifo = self._get_fifo("default")
                        if st.method in ("get", "peek") and not fifo["items"]:
                            yield ("wait_fifo_get", fifo)
                        if fifo["items"]:
                            item = fifo["items"].pop(0) if st.method != "peek" else fifo["items"][0]
                            if st.args:
                                arg_name = st.args.strip()
                                if re.match(r'^[a-zA-Z_]\w*$', arg_name):
                                    env[arg_name] = item
                            if st.method != "peek":
                                self._wake_fifo_waiters(fifo, "wait_put")
                    elif st.method == "set_name" and st.obj:
                        val = str(self._eval_expr(st.args, env, inst, cdef))
                        env[f"__obj_name__{st.obj}"] = val
                    elif st.method == "itoa" and st.obj:
                        val = self._eval_expr(st.args, env, inst, cdef)
                        env[st.obj] = str(val)
                    elif st.method in ("b_transport", "nb_transport_fw", "nb_transport_bw"):
                        for cname, target_cdef in self.classes.items():
                            if st.method in target_cdef.methods:
                                tm = target_cdef.methods[st.method]
                                yield from self._make_task_gen(tm.body, target_cdef, st.method, inst, dict(target_cdef.props))
                                break
                    elif st.method == "start" and st.obj:
                        seq_cls_name = env.get(st.obj) if isinstance(env.get(st.obj), str) else ""
                        if not seq_cls_name or seq_cls_name not in self.classes:
                            for cname in self.classes:
                                if self._is_subclass(cname, "uvm_sequence") and "body" in self.classes[cname].methods:
                                    seq_cls_name = cname
                                    break
                        if seq_cls_name in self.classes and "body" in self.classes[seq_cls_name].methods:
                            scdef = self.classes[seq_cls_name]
                            sm = scdef.methods["body"]
                            yield from self._make_task_gen(sm.body, scdef, "body", inst, dict(scdef.props))
                    elif st.method in cdef.methods and not st.obj:
                        sub_m = cdef.methods[st.method]
                        sub_env = dict(env)
                        if sub_m.params and st.args:
                            call_args = _split_top_level_args(st.args)
                            for p_name, c_arg in zip(sub_m.params, call_args):
                                sub_env[p_name] = self._eval_expr(c_arg, env, inst, cdef)
                        yield from self._make_task_gen(sub_m.body, cdef, st.method, inst, sub_env)

                elif isinstance(st, IfNode):
                    if self._eval_condition(st.cond, env, st.then_body):
                        yield from self._make_task_gen(st.then_body, cdef, method_name, inst, env)
                    elif st.else_body:
                        yield from self._make_task_gen(st.else_body, cdef, method_name, inst, env)

                elif isinstance(st, LoopNode):
                    for vname, val in self._loop_iterations(st, env, inst, cdef):
                        if vname:
                            env[vname] = val
                        yield from self._make_task_gen(st.body, cdef, method_name, inst, env)

                elif isinstance(st, ForkNode):
                    if not st.branches:
                        continue
                    fork_state = {"remaining": len(st.branches), "total": len(st.branches), "join_kind": st.join_kind, "parent": None}

                    def _make_done_cb(fstate):
                        def _cb():
                            fstate["remaining"] -= 1
                            p_gen = fstate["parent"]
                            if p_gen is not None:
                                should_wake = (
                                    (fstate["join_kind"] == "join" and fstate["remaining"] <= 0)
                                    or (fstate["join_kind"] == "join_any")
                                )
                                if should_wake:
                                    fstate["parent"] = None
                                    self._schedule_task(self.sim_time, p_gen)
                        return _cb

                    cb = _make_done_cb(fork_state)
                    for branch in st.branches:
                        bg = self._make_task_gen(branch, cdef, method_name, inst, dict(env), on_done=cb)
                        self._schedule_task(self.sim_time, bg)
                    if st.join_kind in ("join", "join_any"):
                        yield ("wait_fork", fork_state)
        finally:
            if on_done is not None:
                on_done()

    def _run_cooperative_time_wheel(self, tasks: List[Tuple[ComponentInst, ClassDef, MethodDef]]):
        self.pq = []
        for comp, cdef, mdef in tasks:
            self._emit_event(
                kind="phase",
                severity="UVM_INFO",
                file=cdef.file,
                line=mdef.line,
                scope=cdef.name,
                method=mdef.name,
                tag="PH_TRACE",
                msg=f"Executing {comp.full_path}::{mdef.name}()",
                inst_path=comp.full_path,
            )
            g = self._make_task_gen(mdef.body, cdef, mdef.name, comp, dict(cdef.props))
            self._schedule_task(self.sim_time, g)

        steps_guard = 0
        while self.pq and steps_guard < 400 and len(self.events) < self.seen_event_cap:
            steps_guard += 1
            t, _, g = heapq.heappop(self.pq)
            self.sim_time = max(self.sim_time, t)
            try:
                signal = next(g)
                if isinstance(signal, tuple):
                    kind = signal[0]
                    if kind == "delay":
                        self._schedule_task(self.sim_time + signal[1], g)
                    elif kind == "wait_fifo_get":
                        signal[1]["wait_get"].append(g)
                    elif kind == "wait_fifo_put":
                        signal[1]["wait_put"].append(g)
                    elif kind == "wait_fork":
                        fstate = signal[1]
                        if (fstate["join_kind"] == "join" and fstate["remaining"] > 0) or (
                            fstate["join_kind"] == "join_any" and fstate["remaining"] == fstate["total"]
                        ):
                            fstate["parent"] = g
                        else:
                            self._schedule_task(self.sim_time, g)
                else:
                    self._schedule_task(self.sim_time, g)
            except StopIteration:
                pass

        if self.drain_time > 0:
            self.sim_time += self.drain_time

    def run(self) -> List[Dict[str, Any]]:
        # 1. Execute initial blocks (config_db, factory overrides, run_test)
        for fname, _, body in self.initials:
            self._exec_stmts_sync(body, None, "initial", None, {}, file_override=fname)

        if not self.root_test_name or self.root_test_name not in self.classes:
            return self.events

        # 2. Instantiate root test
        real_root = self.type_overrides.get(self.root_test_name, self.root_test_name)
        self.root_comp = ComponentInst(
            inst_name="uvm_test_top",
            full_path="uvm_test_top",
            class_name=real_root,
        )

        # 3. UVM Phases
        self._run_phase_recursive_topdown(self.root_comp, ("build_phase", "build"))
        self._run_phase_recursive_topdown(self.root_comp, ("connect_phase", "connect"))
        self._run_phase_recursive_bottomup(self.root_comp, ("end_of_elaboration_phase", "end_of_elaboration"))
        self._run_phase_recursive_bottomup(self.root_comp, ("start_of_simulation_phase", "start_of_simulation"))

        run_tasks: List[Tuple[ComponentInst, ClassDef, MethodDef]] = []
        self._collect_run_tasks(self.root_comp, run_tasks)
        if run_tasks:
            self._run_cooperative_time_wheel(run_tasks)

        self._run_phase_recursive_topdown(self.root_comp, ("extract_phase", "extract"))
        self._run_phase_recursive_topdown(self.root_comp, ("check_phase", "check"))
        self._run_phase_recursive_topdown(self.root_comp, ("report_phase", "report"))
        self._run_phase_recursive_topdown(self.root_comp, ("final_phase", "final"))

        return self.events


def simulate_example_suite(files_data: List[Dict[str, Any]], meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run the symbolic UVM mini-simulator on a suite's files and return ordered execution events."""
    classes, initials, module_vars = parse_sv_suite(files_data)
    engine = SimEngine(classes, initials, module_vars, files_data, meta)
    return engine.run()
