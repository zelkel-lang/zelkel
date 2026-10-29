import copy
import re
from itertools import count

from src.zelkelc.ast import types
from src.zelkelc.ast.parser import Parser, SyntaxError
from src.zelkelc.lexer import token


class ExpanderError(Exception):
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
            raise ExpanderError("#llvm placeholder out of range")
        if spec == "ty":
            return tys[i]
        return vals[i]

    return _PH.sub(sub, template)


class Expander:
    def __init__(self, ids: count):
        self.ids = ids
        self.expansion_id = 0
        self.macros: dict[str, types.MacroDefinition] = {}

    def run(self, nodes: list[types.Node]) -> list[types.Node]:
        remaining: list[types.Node] = []
        for n in nodes:
            if isinstance(n, types.MacroDefinition):
                if n.name in self.macros:
                    raise ExpanderError(f"macro #{n.name} already defined")
                self.macros[n.name] = n
            else:
                remaining.append(n)
        return self.expand_nodes(remaining, depth=0)

    def expand_nodes(self, nodes: list[types.Node], depth: int) -> list[types.Node]:
        if depth > 64:
            raise ExpanderError("macro recursion limit")
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
        # Builtins
        if call.name == "llvm":
            return [self.expand_llvm(call)]

        macro = self.macros.get(call.name)
        if macro is None:
            raise ExpanderError(f"unknown macro #{call.name}")

        bindings = self.match(macro, call.args)
        transcribed = self.transcribe(macro.body, bindings)

        sub = Parser(transcribed, 0, self.ids)
        try:
            return sub.parse_statements("_macro_", stop_at_rbrace=False)
        except SyntaxError as e:
            raise ExpanderError(f"in expansion of #{call.name}: {e}") from e

    def expand_llvm(self, call: types.MacroCall) -> types.InlineIR:
        tokens = call.args
        if not tokens:
            raise ExpanderError("#llvm requires at least a template string")
        if not isinstance(tokens[0], token.String):
            raise ExpanderError("#llvm first argument must be a string template")

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
            except SyntaxError as e:
                raise ExpanderError(f"#llvm argument parse error: {e}") from e
            if expr is None:
                raise ExpanderError("#llvm expected expression argument")
            arg_exprs.append(expr)
            i = sub.cursor

        eid = self.expansion_id
        self.expansion_id += 1
        return types.InlineIR(template=template, args=arg_exprs, expansion_id=eid)

    def match(
        self, macro: types.MacroDefinition, tokens: list[token.Token]
    ) -> dict[str, list[token.Token]]:
        bindings: dict[str, list[token.Token]] = {}
        i = 0
        for name, kind in macro.params:
            if i > 0:
                if i >= len(tokens) or not isinstance(tokens[i], token.Comma):
                    raise ExpanderError(
                        f"expected ',' between arguments to #{macro.name}"
                    )
                i += 1

            sub = Parser(tokens, i, self.ids)
            try:
                match kind:
                    case "expr":
                        expr = sub.parse_expression()
                        if expr is None:
                            raise SyntaxError("expected expression")
                        bindings[name] = [token.Interpolated(expr)]

                    case "ident":
                        ident = sub.expect_type(token.Identifier)
                        bindings[name] = [ident]

                    case "type":
                        typ = sub.parse_type(False)
                        type_name = {
                            types.Integer64: "i64",
                            types.Float64: "f64",
                            types.String: "str",
                            types.Void: "void",
                        }.get(typ, "unknown")
                        bindings[name] = [token.Identifier(type_name)]

                    case "tt":
                        start = sub.cursor
                        depth = 0
                        while sub.cursor < len(tokens):
                            t = tokens[sub.cursor]
                            if isinstance(t, token.Comma) and depth == 0:
                                break
                            if isinstance(t, (token.LParen, token.LBrace)):
                                depth += 1
                            elif isinstance(t, (token.RParen, token.RBrace)):
                                depth -= 1
                            sub.cursor += 1
                        bindings[name] = tokens[start : sub.cursor]

                    case _:
                        raise ExpanderError(f"unknown fragment kind {kind}")
            except SyntaxError as e:
                raise ExpanderError(
                    f"failed to match '{name}:{kind}' of #{macro.name}: {e}"
                ) from e
            i = sub.cursor

        if i != len(tokens):
            raise ExpanderError(f"unexpected tokens in call to #{macro.name}")
        return bindings

    def transcribe(
        self, template: list[token.Token], bindings: dict[str, list[token.Token]]
    ) -> list[token.Token]:
        hygiene_map: dict[str, str] = {}
        eid = next(self.ids)
        j = 0
        while j < len(template):
            t = template[j]
            if (
                isinstance(t, token.Identifier)
                and t.value in ("val", "var")
                and j + 1 < len(template)
                and isinstance(template[j + 1], token.Identifier)
            ):
                old = template[j + 1].value
                if old not in hygiene_map:
                    hygiene_map[old] = f"{old}__{eid}"
            j += 1

        out: list[token.Token] = []
        i = 0
        while i < len(template):
            t = template[i]
            if isinstance(t, token.Dollar) and i + 1 < len(template):
                nxt = template[i + 1]
                if isinstance(nxt, token.Identifier) and nxt.value in bindings:
                    for b in bindings[nxt.value]:
                        if isinstance(b, token.Interpolated):
                            out.append(token.Interpolated(copy.deepcopy(b.node)))
                        else:
                            out.append(b)
                    i += 2
                    continue

            if isinstance(t, token.Identifier) and t.value in hygiene_map:
                out.append(token.Identifier(hygiene_map[t.value]))
            else:
                out.append(t)
            i += 1
        return out
