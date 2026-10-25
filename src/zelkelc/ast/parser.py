import src.zelkelc.lexer.token as token
import src.zelkelc.ast.types as types

from typing import Optional

class Parser:
    tokens: list[token.Token]
    cursor: int
        
    def __init__(self, tokens: list[token.Token], cursor: int):
        self.tokens = tokens
        self.cursor = cursor
    
    def expect(self, tok: token.Token): 
        if not self.tokens[self.cursor] == tok:
            print(f"Expected {tok}, but found {self.tokens[self.cursor]}")
            exit(1)
        self.cursor += 1
            
    def expect_type(self, tok_type: token.Token) -> token.Token:
        if not type(self.tokens[self.cursor]) == tok_type:
            print(f"Expected {tok_type}, but found {type(self.tokens[self.cursor])}")
            exit(1)
        self.cursor += 1
        return self.tokens[self.cursor - 1]
    
    def current(self, tok: token.Token): 
        if not self.tokens[self.cursor] == tok:
            return False
        return True

    def current_type(self, tok_type: token.Token) -> bool:
        if not type(self.tokens[self.cursor]) == tok_type:
            return False
        return True

    def parse_type(self, is_return_type: bool) -> types.Value:
        identifier = self.expect_type(token.Identifier)
        match identifier.value:
            case "str":
                return types.String
            case "i64":
                return types.Integer64
            case "void" if is_return_type == True:
                return types.Void
            case _:
                print("Invalid type found in parse_type")
                exit(1)

    def parse(self):
        ast: list[types.FunctionDeclaration | types.ClassDeclaration] = []
        
        while self.cursor < len(self.tokens):
            t = self.tokens[self.cursor]
            
            match t:
                case token.Identifier():
                    match t.value:
                        case "fn":
                            ast.append(self.parse_function_declaration("_main.zk_")) # TODO: replace with actual filepath to the file
                        case "struct":
                            ast.append(self.parse_struct_declaration("_main.zk_"))
                        case "class":
                            ast.append(self.parse_class_declaration("_main.zk_"))
                        case _:
                            print(f"Invalid keyword in global {t.value}")
                            exit(1)
                case _:
                    print(f"Invalid token found while parsing global {t}")
                    exit(1)
                            
        
        return ast

    def parse_struct_declaration(self, path: str) -> types.StructDeclaration:
        self.expect(token.Identifier("struct"))
        name = self.expect_type(token.Identifier).value
        self.expect(token.LBrace())
        
        members: list[types.MemberDeclaration] = []
                
        while self.cursor < len(self.tokens) and not self.tokens[self.cursor] == token.RBrace():
            t = self.tokens[self.cursor]
            
            match t:
                case token.Identifier():
                    match t.value:
                        case "val":
                            members.append(self.parse_member_declaration(False, len(members)))
                        case "var":
                            members.append(self.parse_member_declaration(True, len(members)))
                        case _:
                            print(f"Invalid keyword in struct body {t.value}")
                            exit(1)
                case _:
                    print(f"Invalid token found while parsing class declaration: {t}")
                    exit(1)
        
        self.expect(token.RBrace())
        
        return types.StructDeclaration(
            name,
            members,
            irname = f"{path}.s_{name}"
        )
    
    def parse_member_declaration(self, mutable: bool, member_idx: int) -> types.MemberDeclaration:
        if mutable:
            self.expect(token.Identifier("var"))
        else:
            self.expect(token.Identifier("val"))
        
        name = self.expect_type(token.Identifier).value
        
        self.expect(token.Colon())
        typ = self.parse_type(False)
        
        return types.MemberDeclaration(
            name,
            mutable,
            typ,
            real_idx = member_idx
        )
    
    def parse_class_declaration(self, path: str) -> types.ClassDeclaration:
        self.expect(token.Identifier("class"))
        name = self.expect_type(token.Identifier).value
        self.expect(token.LBrace())
        
        members: list[types.ValueDeclaration] = []
        methods: list[types.FunctionDeclaration] = []
        
        while self.cursor < len(self.tokens) and not self.tokens[self.cursor] == token.RBrace():
            t = self.tokens[self.cursor]

            match t:
                case token.Identifier():
                    match t.value:
                        case "fn":
                            methods.append(self.parse_function_declaration(f"{path}.c_{name}"))
                        case "val":
                            members.append(self.parse_member_declaration(False, len(members)))
                        case "var":
                            members.append(self.parse_member_declaration(True, len(members)))
                        case _:
                            print(f"Invalid keyword in class body {t.value}")
                            exit(1)
                case _:
                    print(f"Invalid token found while parsing class declaration: {t}")
                    exit(1)
        
        self.expect(token.RBrace())
        
        return types.ClassDeclaration(
            name,
            members,
            methods,
            irname = f"{path}.c_{name}"
        )
    
    def parse_function_declaration(self, path: str) -> types.FunctionDeclaration:
        self.expect(token.Identifier("fn"))
        name = self.expect_type(token.Identifier).value
        self.expect(token.LParen())
        
        args: dict[str, types.Value] = {}
        while self.cursor < len(self.tokens) and not self.current(token.RParen()):
            arg_name = self.expect_type(token.Identifier).value
            
            self.expect(token.Colon())
            typ = self.parse_type(False)
            args[arg_name] = typ
            
            if not self.current(token.Comma()):
                break
            else:
                self.expect(token.Comma())
        
        self.expect(token.RParen())
        
        self.expect(token.Arrow())
        typ = self.parse_type(True)
        
        self.expect(token.LBrace())
        
        body: list[types.Node] = []
        hasReturn: bool = False # TODO: should be replaced with real return tree checking, this is not a good system
        
        while self.cursor < len(self.tokens) and not self.tokens[self.cursor] == token.RBrace():
            t = self.tokens[self.cursor]
            
            match t:
                case token.Identifier():
                    match t.value:
                        case "fn":
                            body.append(self.parse_function_declaration(f"{path}.f_{name}"))
                        case "val":
                            body.append(self.parse_value_declaration(False))
                        case "var":
                            body.append(self.parse_value_declaration(True))
                        case "return":
                            body.append(self.parse_return())
                            hasReturn = True
                        case _:
                            print(f"Invalid keyword in function body {t.value}")
                            exit(1)
                case _:
                    #TODO: expression statement
                    print(f"implement expression statement: {t}")
                    exit(1)
        
        if hasReturn == False:
            print("Function must have return")
            exit(1)
        
        self.expect(token.RBrace())
        
        irname = f"{path}.f_{name}_{typ}"
        if name == "main":
            irname = "main"
        
        return types.FunctionDeclaration(
            name = name,
            typ = typ,
            args = args,
            body = body,
            irname = irname
        )
    
    def parse_return(self) -> types.ReturnStatement:
        self.expect(token.Identifier("return"))
        
        expr: Optional[types.Expression] = None    
        if not self.current(token.RBrace()):
            expr = self.parse_expression()

        return types.ReturnStatement(
            expr
        )
    
    def parse_value_declaration(self, mutable: bool) -> types.ValueDeclaration:
        if mutable:
            self.expect(token.Identifier("var"))
        else:
            self.expect(token.Identifier("val"))
        
        name = self.expect_type(token.Identifier).value
        
        self.expect(token.Colon())
        typ = self.parse_type(False)
        
        self.expect(token.Equals())
        
        expr = self.parse_expression()
        
        return types.ValueDeclaration(
            name,
            mutable,
            typ,
            expr,
            irname = f"v_{self.cursor}_{name}"
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
                print(f"Invalid unary operator: {op}")
                exit(1)
            operand = self.parse_unary_expression()
            return types.UnaryExpression(operand, op, operand.typ)

        return self.parse_primary_expression()

    def parse_primary_expression(self) -> Optional[types.Expression]:
        t = self.tokens[self.cursor]

        match t:
            case token.Identifier():
                self.cursor += 1
                
                if self.current(token.LParen()):
                    self.cursor += 1
                    args: list[types.Expression] = []
                    while self.cursor < len(self.tokens) and self.tokens[self.cursor] != token.RParen():
                        if len(args) != 0:
                            self.expect(token.Comma())
                        args.append(self.parse_expression())
                    
                    self.expect(token.RParen())
                    return types.PrimaryExpression(types.FunctionCall(t.value, args, None), types.FunctionCall)
                else:
                    return types.PrimaryExpression(types.VariableRef(t.value, None), types.VariableRef)

            case token.Integer():
                self.cursor += 1
                return types.PrimaryExpression(types.Integer64(t.value), types.Integer64)

            case token.String():
                self.cursor += 1
                return types.PrimaryExpression(types.String(t.value), types.String)

            case token.LParen():
                self.expect(token.LParen())
                expr = self.parse_expression()
                self.expect(token.RParen())
                return expr

            case _:
                return None

    def _operator_precedence(self, op: str) -> int:
        table = {
            "||": 1,
            "&&": 2,
            "==": 3, "!=": 3,
            "<": 4, "<=": 4, ">": 4, ">=": 4,
            "+": 5, "-": 5,
            "*": 6, "/": 6, "%": 6,
        }
        
        return table.get(op, 0)