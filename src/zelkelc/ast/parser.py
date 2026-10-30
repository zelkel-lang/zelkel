from itertools import count

from src.zelkelc.ast import types
from src.zelkelc.lexer import token


class SyntaxError(Exception):
    pass


class Parser:
    tokens: list[token.Token]
    cursor: int
    ids: count

    def __init__(self, tokens: list[token.Token], cursor: int, ids: count):
        self.tokens = tokens
        self.cursor = cursor
        self.ids = ids

    def expect(self, tok: token.Token):
        if self.tokens[self.cursor] != tok:
            raise SyntaxError(f"Expected {tok}, but found {self.tokens[self.cursor]}")
        self.cursor += 1

    def expect_type(self, tok_type: token.Token) -> token.Token:
        if type(self.tokens[self.cursor]) is not tok_type:
            raise SyntaxError(
                f"Expected {tok_type}, but found {type(self.tokens[self.cursor])}"
            )
        self.cursor += 1
        return self.tokens[self.cursor - 1]

    def current(self, tok) -> bool:
        return self.cursor < len(self.tokens) and self.tokens[self.cursor] == tok

    def current_type(self, tok_type) -> bool:
        return (
            self.cursor < len(self.tokens)
            and type(self.tokens[self.cursor]) is tok_type
        )

    @staticmethod
    def type_to_str(typ: types.Value, is_return_type: bool) -> types.Value:
        match typ:
            case types.String:
                return "str"
            case types.Integer64:
                return "i64"
            case types.Float64:
                return "f64"
            case types.Void if is_return_type:
                return "void"
            case _:
                raise SyntaxError(f"Invalid type found in type_to_str: {typ}")

    def parse_type(self, is_return_type: bool) -> types.Value:
        identifier = self.expect_type(token.Identifier)
        match identifier.value:
            case "str":
                return types.String
            case "i64":
                return types.Integer64
            case "f64":
                return types.Float64
            case "void" if is_return_type:
                return types.Void
            case _:
                raise SyntaxError(
                    f"Invalid type found in parse_type: {identifier.value}"
                )

    def parse_item(self, path: str = "_main.zk_") -> types.Node:
        t = self.tokens[self.cursor]

        match t:
            case token.Identifier():
                match t.value:
                    case "fn":
                        return self.parse_function_declaration(path)
                    case "struct":
                        return self.parse_struct_declaration(path)
                    case "class":
                        return self.parse_class_declaration(path)
                    case _:
                        raise SyntaxError(f"Invalid keyword in global {t.value}")
            case token.Pound():
                return self.parse_pound()
            case _:
                raise SyntaxError(f"Invalid token found while parsing global {t}")

    def parse_items(self) -> list[types.Node]:
        items = []
        while self.cursor < len(self.tokens):
            items.append(self.parse_item())
        return items

    def parse(self):
        return self.parse_items()

    def take_delimited(self) -> list[token.Token]:
        if self.current(token.LParen()):
            open_t, _close_t = token.LParen(), token.RParen()
        elif self.current(token.LBrace()):
            open_t, _close_t = token.LBrace(), token.RBrace()
        else:
            raise SyntaxError("Expected '(' or '{' to start delimited token tree")
        self.expect(open_t)
        depth, start = 1, self.cursor
        while depth:
            if self.cursor >= len(self.tokens):
                raise SyntaxError("unclosed delimited group")
            t = self.tokens[self.cursor]
            if isinstance(t, (token.LParen, token.LBrace)):
                depth += 1
            elif isinstance(t, (token.RParen, token.RBrace)):
                depth -= 1
            self.cursor += 1
        return self.tokens[start : self.cursor - 1]

    def parse_pound(self) -> types.Node:
        self.expect(token.Pound())
        ident = self.expect_type(token.Identifier)
        if ident.value == "fn":
            return self.parse_macro_definition()
        return self.parse_macro_call(ident)

    def parse_macro_definition(self) -> types.MacroDefinition:
        name = self.expect_type(token.Identifier).value

        self.expect(token.LParen())
        params: list[tuple[str, str]] = []
        while not self.current(token.RParen()):
            if params:
                self.expect(token.Comma())
            self.expect(token.Dollar())
            pname = self.expect_type(token.Identifier).value
            self.expect(token.Colon())
            kind = self.expect_type(token.Identifier).value
            if kind not in ("expr", "ident", "type", "tt"):
                raise SyntaxError(f"Unknown macro fragment kind: {kind}")
            params.append((pname, kind))
        self.expect(token.RParen())

        body = self.take_delimited()
        return types.MacroDefinition(name=name, params=params, body=body)

    def parse_macro_call(self, ident: token.Identifier) -> types.MacroCall:
        args = self.take_delimited()
        return types.MacroCall(name=ident.value, args=args)

    def parse_struct_declaration(self, path: str) -> types.StructDeclaration:
        self.expect(token.Identifier("struct"))
        name = self.expect_type(token.Identifier).value
        self.expect(token.LBrace())

        members: list[types.MemberDeclaration] = []

        while (
            self.cursor < len(self.tokens)
            and self.tokens[self.cursor] != token.RBrace()
        ):
            t = self.tokens[self.cursor]

            match t:
                case token.Identifier():
                    match t.value:
                        case "val":
                            members.append(
                                self.parse_member_declaration(False, len(members))
                            )
                        case "var":
                            members.append(
                                self.parse_member_declaration(True, len(members))
                            )
                        case _:
                            raise SyntaxError(
                                f"Invalid keyword in struct body {t.value}"
                            )
                case _:
                    raise SyntaxError(
                        f"Invalid token found while parsing class declaration: {t}"
                    )

        self.expect(token.RBrace())

        return types.StructDeclaration(name, members, irname=f"{path}.s_{name}")

    def parse_member_declaration(
        self, mutable: bool, member_idx: int
    ) -> types.MemberDeclaration:
        if mutable:
            self.expect(token.Identifier("var"))
        else:
            self.expect(token.Identifier("val"))

        name = self.expect_type(token.Identifier).value

        self.expect(token.Colon())
        typ = self.parse_type(False)

        return types.MemberDeclaration(name, mutable, typ, real_idx=member_idx)

    def parse_class_declaration(self, path: str) -> types.ClassDeclaration:
        self.expect(token.Identifier("class"))
        name = self.expect_type(token.Identifier).value
        self.expect(token.LBrace())

        members: list[types.ValueDeclaration] = []
        methods: list[types.FunctionDeclaration] = []

        while (
            self.cursor < len(self.tokens)
            and self.tokens[self.cursor] != token.RBrace()
        ):
            t = self.tokens[self.cursor]

            match t:
                case token.Identifier():
                    match t.value:
                        case "fn":
                            methods.append(
                                self.parse_function_declaration(f"{path}.c_{name}")
                            )
                        case "val":
                            members.append(
                                self.parse_member_declaration(False, len(members))
                            )
                        case "var":
                            members.append(
                                self.parse_member_declaration(True, len(members))
                            )
                        case _:
                            raise SyntaxError(
                                f"Invalid keyword in class body {t.value}"
                            )
                case _:
                    raise SyntaxError(
                        f"Invalid token found while parsing class declaration: {t}"
                    )

        self.expect(token.RBrace())

        return types.ClassDeclaration(name, members, methods, irname=f"{path}.c_{name}")

    def parse_statement(self, path: str) -> types.Node:
        t = self.tokens[self.cursor]

        match t:
            case token.Identifier():
                match t.value:
                    case "fn":
                        return self.parse_function_declaration(path)
                    case "val":
                        return self.parse_value_declaration(False)
                    case "var":
                        return self.parse_value_declaration(True)
                    case "return":
                        return self.parse_return()
                    case _:
                        if self.tokens[self.cursor + 1]:
                            return self.parse_value_assignment()

                        raise SyntaxError(f"Invalid keyword in function body {t.value}")
            case token.Pound():
                return self.parse_pound()
            case _:
                # TODO: expression statement
                raise SyntaxError(f"implement expression statement: {t}")

    def parse_statements(self, path: str, stop_at_rbrace: bool) -> list[types.Node]:
        body = []
        while self.cursor < len(self.tokens):
            if stop_at_rbrace and self.current(token.RBrace()):
                break
            body.append(self.parse_statement(path))
        return body

    def parse_function_declaration(self, path: str) -> types.FunctionDeclaration:
        self.expect(token.Identifier("fn"))
        name = self.expect_type(token.Identifier).value
        self.expect(token.LParen())

        args: dict[str, types.Value] = {}
        while self.cursor < len(self.tokens) and not self.current(token.RParen()):
            arg_name = self.expect_type(token.Identifier).value

            if arg_name == "self":
                args[arg_name] = None
            else:
                self.expect(token.Colon())
                typ = self.parse_type(False)
                args[arg_name] = typ

            if not self.current(token.Comma()):
                break
            else:
                self.expect(token.Comma())

        self.expect(token.RParen())
        
        label = None
        if self.current(token.Colon()):
            self.expect(token.Colon())
            label = self.expect_type(token.Identifier)
            
        self.expect(token.Arrow())
        typ = self.parse_type(True)

        self.expect(token.LBrace())
        body = self.parse_statements(f"{path}.f_{name}", stop_at_rbrace=True)
        self.expect(token.RBrace())

        irname = f"{path}.f_{name}_{self.type_to_str(typ, True)}"
        if name == "main":
            irname = "zkmain"

        return types.FunctionDeclaration(name, label, typ, args, body, irname)

    def parse_return(self) -> types.ReturnStatement:
        self.expect(token.Identifier("return"))

        expr: types.Expression | None = None
        if not self.current(token.RBrace()):
            expr = self.parse_expression()

        return types.ReturnStatement(expr)

    def parse_value_declaration(self, mutable: bool) -> types.ValueDeclaration:
        if mutable:
            self.expect(token.Identifier("var"))
        else:
            self.expect(token.Identifier("val"))

        name = self.expect_type(token.Identifier).value

        self.expect(token.Colon())
        typ = self.parse_type(False)

        self.expect(token.Assigner("="))

        expr = self.parse_expression()

        return types.ValueDeclaration(
            name, mutable, typ, expr, irname=f"v_{next(self.ids)}_{name}"
        )

    def parse_value_assignment(self) -> types.ValueAssignment:
        name = self.expect_type(token.Identifier).value

        assigner = self.expect_type(token.Assigner).value
        match assigner:
            case "=":
                self.expect(token.Assigner("="))
            case "+=":
                self.expect(token.Assigner("+="))
            case "-=":
                self.expect(token.Assigner("-="))
            case "*=":
                self.expect(token.Assigner("*="))
            case "/=":
                self.expect(token.Assigner("/="))
            case _:
                raise SyntaxError(f"Unknown assignment operator '{assigner}' found while parsing")

        if assigner == "=":
            expr = self.parse_expression()
        else:
            right = self.parse_expression()
            expr = types.BinaryExpression(
                types.PrimaryExpression(
                    types.VariableRef(name, True, None, None),
                    None
                ),
                right,
                assigner[0],
                right.typ,
            )
            
        return types.ValueAssignment(
            name,
            assigner,
            None,
            expr,
            None,
        )

    def parse_expression(self) -> types.Expression:
        return self.parse_binary_expression(0)

    def parse_binary_expression(self, min_precedence: int = 0) -> types.Expression:
        left = self.parse_unary_expression()

        while self.current_type(token.Operator):
            op_token = self.tokens[self.cursor]
            op = op_token.value
            precedence = self._operator_precedence(op)

            if precedence < min_precedence:
                break

            self.cursor += 1

            right = self.parse_binary_expression(precedence + 1)

            left = types.BinaryExpression(left, right, op, left.typ)

        return left

    def parse_unary_expression(self) -> types.Expression:
        if self.current_type(token.Operator):
            op = self.expect_type(token.Operator).value

            if op not in ("-", "+"):
                raise SyntaxError(f"Invalid unary operator: {op}")
            operand = self.parse_unary_expression()
            return types.UnaryExpression(operand, op, operand.typ)

        return self.parse_primary_expression()

    def parse_primary_expression(self) -> types.Expression | None:
        t = self.tokens[self.cursor]

        match t:
            case token.Identifier():
                self.cursor += 1

                if self.current(token.LParen()):
                    self.cursor += 1
                    args: list[types.Expression] = []
                    while (
                        self.cursor < len(self.tokens)
                        and self.tokens[self.cursor] != token.RParen()
                    ):
                        if len(args) != 0:
                            self.expect(token.Comma())
                        args.append(self.parse_expression())

                    self.expect(token.RParen())
                    return types.PrimaryExpression(
                        types.FunctionCall(t.value, None, None, args),
                        types.FunctionCall,
                    )
                else:
                    return types.PrimaryExpression(
                        types.VariableRef(t.value, None, None, None), types.VariableRef
                    )

            case token.Integer():
                self.cursor += 1
                return types.PrimaryExpression(
                    types.Integer64(t.value), types.Integer64
                )

            case token.Float():
                self.cursor += 1
                return types.PrimaryExpression(types.Float64(t.value), types.Float64)

            case token.String():
                self.cursor += 1
                return types.PrimaryExpression(types.String(t.value), types.String)

            case token.LParen():
                self.expect(token.LParen())
                expr = self.parse_expression()
                self.expect(token.RParen())
                return expr

            case token.Interpolated():
                self.cursor += 1
                return t.node

            case _:
                return None

    def _operator_precedence(self, op: str) -> int:
        table = {
            "||": 1,
            "&&": 2,
            "==": 3,
            "!=": 3,
            "<": 4,
            "<=": 4,
            ">": 4,
            ">=": 4,
            "+": 5,
            "-": 5,
            "*": 6,
            "/": 6,
            "%": 6,
        }

        return table.get(op, 0)
