import sys

from src.zelkelc.ast import types


class IRTable:
    top: str
    structs: str
    struct_functions: str
    global_functions: str
    bottom: str

    def __init__(self):
        self.top = ""
        self.structs = ""
        self.struct_functions = ""
        self.global_functions = ""
        self.bottom = ""


class Codegen:
    ast: list[types.FunctionDeclaration | types.ClassDeclaration]
    ir: IRTable
    temp_counter: int

    def __init__(self, ast: list[types.FunctionDeclaration | types.ClassDeclaration]):
        self.ast = ast
        self.ir = IRTable()
        self.temp_counter = 0

    def generate(self):
        for node in self.ast:
            match node:
                case types.StructDeclaration():
                    self.gen_struct_declaration(node)
                case types.ClassDeclaration():
                    self.gen_class_declaration(node)
                case types.FunctionDeclaration():
                    self.ir.global_functions += self.gen_function_declaration(node)
                case types.MacroCall():
                    self.ir.top = rf"{node.body}" + "\n" + self.ir.top
                case _:
                    print(f"Invalid node found during codegen {type(node)}")
                    sys.exit(1)

        self.gen_main_function()

        return (
            self.ir.top
            + "\n"
            + self.ir.structs
            + "\n"
            + self.ir.struct_functions
            + "\n"
            + self.ir.global_functions
            + "\n"
            + self.ir.bottom
        )

    def gen_main_function(self):
        self.ir.bottom += "define i32 @main() {\n"
        self.ir.bottom += "entry:\n"
        self.ir.bottom += "call void @zkmain()\n"
        self.ir.bottom += "ret i32 0\n"
        self.ir.bottom += "}\n"

    def gen_struct_declaration(self, node: types.StructDeclaration):
        members_str = ""
        for i, m in enumerate(node.members):
            members_str += f"{', ' if i != 0 else ''}{m.typ.to_llvm()}"

        self.ir.structs += f"\n%{node.irname} = type " + "{ " + members_str + " }"

    def gen_class_declaration(self, node: types.ClassDeclaration):
        members_str = ""
        for i, m in enumerate(node.members):
            members_str += f"{', ' if i != 0 else ''}{m.typ.to_llvm()}"

        self.ir.structs += f"\n%{node.irname} = type " + "{ " + members_str + " }"

        for func in node.methods:
            self.ir.struct_functions += self.gen_function_declaration(func)

    def gen_function_declaration(self, node: types.FunctionDeclaration) -> str:
        args_str = ""
        for i, (name, typ) in enumerate(node.args.items()):
            args_str += f"{', ' if i != 0 else ''}{typ.to_llvm()} %{name}"

        ir = f"\ndefine {node.typ.to_llvm()!s} @{node.irname}({args_str}) " + "{"
        ir += "\nentry:"

        for child_node in node.body:
            match child_node:
                case types.ValueDeclaration():
                    ir += self.gen_value_declaration(child_node)
                case types.MacroCall():
                    ir += "\n" + rf"{child_node.body}"
                case types.ReturnStatement():
                    ir += self.gen_return_statement(child_node)
                case _:
                    print(
                        f"gen_function_declaration() {type(child_node)} is unimplemented"
                    )
                    sys.exit(1)

        return ir + "\n}\n"

    def gen_value_declaration(self, node: types.ValueDeclaration) -> str:
        ir = ""

        count, expr = self.gen_expression(node.expr)
        ir += expr

        match node.typ:
            case types.Integer64:
                if node.mutable:
                    ir += f"\n%{node.irname} = alloca i64, align 8"
                    ir += f"\nstore i64 %{count}, i64* %{node.irname}, align 8"
                else:
                    ir += f"\n%{node.irname} = add i64 %{count}, 0"
            case types.Float64:
                if node.mutable:
                    ir += f"\n%{node.irname} = alloca double, align 8"
                    ir += f"\nstore double %{count}, double* %{node.irname}, align 8"
                else:
                    ir += f"\n%{node.irname} = fadd double %{count}, 0.0"
            case _:
                print(f"gen_value_declaration() for {node.typ} is unimplemented")
                sys.exit(1)

        return ir
    
    def gen_return_statement(self, node: types.ReturnStatement) -> str:
        print(node)
        print(node.expr)
        
        ir = ""
        
        if node.expr:
            count, expr = self.gen_expression(node.expr)
            ir += expr
            ir += f"\nret {node.expr.typ.to_llvm()} %{count}"
        else:
            ir += "\nret void"
            
        return ir

    def make_i64_op(self, sign: str) -> str:
        match sign:
            case "+":
                return "add"
            case "-":
                return "sub"
            case "*":
                return "mul"
            case _:
                print(f"Cannot do operation '{sign}' on i64")
                sys.exit(1)

    def make_f64_op(self, sign: str) -> str:
        match sign:
            case "+":
                return "fadd"
            case "-":
                return "fsub"
            case "*":
                return "fmul"
            case "/":
                return "fdiv"
            case _:
                print(f"Cannot do operation '{sign}' on f64")
                sys.exit(1)

    def gen_expression(self, node: types.Expression) -> tuple[str, str]:
        ir = ""

        match type(node):
            case types.BinaryExpression:
                left_irname, left = self.gen_expression(node.left)
                right_irname, right = self.gen_expression(node.right)

                ir += left + right

                match node.left.typ:
                    case types.Integer64:
                        ir += f"\n%{self.temp_counter} = {self.make_i64_op(node.op)} i64 %{left_irname}, %{right_irname}"
                        self.temp_counter += 1
                    case types.Float64:
                        ir += f"\n%{self.temp_counter} = {self.make_f64_op(node.op)} double %{left_irname}, %{right_irname}"
                        self.temp_counter += 1
                    case types.VariableRef:
                        match node.left.value.typ:
                            case types.Integer64:
                                ir += f"\n%{self.temp_counter} = {self.make_i64_op(node.op)} i64 %{left_irname}, %{right_irname}"
                                self.temp_counter += 1
                            case types.Float64:
                                ir += f"\n%{self.temp_counter} = {self.make_f64_op(node.op)} double %{left_irname}, %{right_irname}"
                                self.temp_counter += 1
                            case _:
                                print(
                                    f"gen_expression() for BinaryExpression left operand variable type '{node.left.value.typ}' is unimplemented"
                                )
                    case _:
                        print(
                            f"gen_expression() for BinaryExpression for {node.left.typ}"
                        )
                        sys.exit(1)
            case types.UnaryExpression:
                print("gen_expression() for UnaryExpression unimplemented")
                sys.exit(1)

            case types.PrimaryExpression:
                match type(node.value):
                    case types.Integer64:
                        ir += f"\n%{self.temp_counter} = add i64 {node.value.value}, 0"
                        self.temp_counter += 1
                    case types.Float64:
                        ir += f"\n%{self.temp_counter} = fadd double {node.value.value}, 0.0"
                        self.temp_counter += 1
                    case types.VariableRef:
                        return node.value.irname, ir
                    case _:
                        print(
                            f"gen_expression() for PrimaryExpression for {type(node.value)}"
                        )
                        sys.exit(1)
            case _:
                print(f"Invalid expression types found during codegen: {node}")
                sys.exit(1)

        return str(self.temp_counter - 1), ir
