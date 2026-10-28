import re
from itertools import count

from src.zelkelc.ast import types
from src.zelkelc.ast.parser import ParseError, Parser
from src.zelkelc.lexer import token


class MacroError(Exception):
    pass


_PH = re.compile(r"\{\{|\}\}|\{(\d*)(?::(\w+))?\}")


def render_llvm(template: str, vals: list[str], tys: list[str], eid: int) -> str:
    auto = iter(range(len(vals)))

    def sub(m: re.Match) -> str:
        if m.group(0) == "{{":
            return "{"
        if m.group(0) == "}}":
            return "}"
        idx, spec = m.group(1), m.group(2)
        if spec == "id":
            return str(eid)
        i = int(idx) if idx else next(auto)
        if i >= len(vals):
            raise MacroError("#llvm placeholder out of range")
        if spec == "ty":
            return tys[i]
        return vals[i]

    return _PH.sub(sub, template)


class Expander:
    def __init__(self, ids: count):
        self.ids = ids
        self.expansion_id = 0

    def run(self, nodes: list[types.Node]) -> list[types.Node]:
        return self.expand_nodes(nodes, depth=0)

    def expand_nodes(self, nodes: list[types.Node], depth: int) -> list[types.Node]:
        if depth > 64:
            raise MacroError("macro recursion limit")
        out: list[types.Node] = []
        for n in nodes:
            if isinstance(n, types.MacroCall):
                expanded = self.expand_call(n)
                out.extend(self.expand_nodes(expanded, depth + 1))
            elif isinstance(n, types.FunctionDeclaration):
                n.body = self.expand_nodes(n.body, depth)
                out.append(n)
            elif isinstance(n, types.ClassDeclaration):
                for m in n.methods:
                    m.body = self.expand_nodes(m.body, depth)
                out.append(n)
            else:
                out.append(n)
        return out

    def expand_call(self, call: types.MacroCall) -> list[types.Node]:
        if call.name == "llvm":
            return [self.expand_llvm(call)]
        raise MacroError(f"unknown macro #{call.name}")

    def expand_llvm(self, call: types.MacroCall) -> types.InlineIR:
        tokens = call.args
        if not tokens:
            raise MacroError("#llvm requires at least a template string")
        if not isinstance(tokens[0], token.String):
            raise MacroError("#llvm first argument must be a string template")

        template = tokens[0].value
        arg_exprs: list[types.Expression] = []
        i = 1
        while i < len(tokens):
            if isinstance(tokens[i], token.Comma):
                i += 1
                continue
            sub = Parser(tokens, i, self.ids)
            try:
                expr = sub.parse_expression()
            except ParseError as e:
                raise MacroError(f"#llvm argument parse error: {e}") from e
            if expr is None:
                raise MacroError("#llvm expected expression argument")
            arg_exprs.append(expr)
            i = sub.cursor

        eid = self.expansion_id
        self.expansion_id += 1
        return types.InlineIR(template=template, args=arg_exprs, expansion_id=eid)
