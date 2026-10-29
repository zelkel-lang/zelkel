import struct
import sys

from src.zelkelc.ast import types
from src.zelkelc.expander.expander import render_llvm
from src.zelkelc.ast.parser import Parser


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
                case types.InlineIR():
                    self.ir.top = self.gen_inline_ir(node, is_top=True) + "\n" + self.ir.top
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
        
    def gen_inline_ir(self, node: types.InlineIR, is_top: bool) -> str:
        vals: list[str] = []
        tys: list[str] = []
        prefix = ""
        for arg in node.args:
            operand, expr_ir = self.gen_expression(arg)
            prefix += expr_ir
            vals.append(operand)
            tys.append(self.llvm_type(arg.typ))

        rendered = render_llvm(node.template, vals, tys, node.expansion_id)
        if is_top:
            return rendered
        return (
            prefix + ("\n" if prefix and not prefix.endswith("\n") else "") + rendered
        )

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
                case types.ValueAssignment():
                    ir += self.gen_value_assignment(child_node)
                case types.InlineIR():
                    ir += "\n" + self.gen_inline_ir(child_node, is_top=False)
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

        operand, expr = self.gen_expression(node.expr)
        ir += expr

        match node.typ:
            case types.Integer64:
                if node.mutable:
                    ir += f"\n%{node.irname} = alloca i64, align 8"
                    ir += f"\nstore i64 {operand}, i64* %{node.irname}, align 8"
                else:
                    ir += f"\n%{node.irname} = add i64 {operand}, 0"
            case types.Float64:
                if node.mutable:
                    ir += f"\n%{node.irname} = alloca double, align 8"
                    ir += f"\nstore double {operand}, double* %{node.irname}, align 8"
                else:
                    ir += f"\n%{node.irname} = fadd double {operand}, 0.0"
            case _:
                print(f"gen_value_declaration() for {node.typ} is unimplemented")
                sys.exit(1)

        return ir
    
    def gen_value_assignment(self, node: types.ValueAssignment) -> str:
        ir = ""
        
        operand, expr = self.gen_expression(node.expr)
        ir += expr
        
        match node.typ:
            case types.Integer64:
                ir += f"\nstore i64 {operand}, i64* %{node.irname}, align 8"
            case types.Float64:
                ir += f"\nstore double {operand}, double* %{node.irnmae}, align 8"
            case _:
                print(f"gen_value_assignment() for {node.typ} is unimplemented")
                sys.exit(1)
        
        return ir

    def gen_return_statement(self, node: types.ReturnStatement) -> str:
        ir = ""

        if node.expr:
            operand, expr = self.gen_expression(node.expr)
            ir += expr
            ir += f"\nret {self.llvm_type(node.expr.typ)} {operand}"
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
            case "%":
                return "frem"
            case _:
                print(f"Cannot do operation '{sign}' on f64")
                sys.exit(1)

    def get_function_args_llvm(self, node: types.FunctionCall) -> tuple[str, str]:
        ir = ""
        args_str = ""
        for i, arg in enumerate(node.args):
            if i != 0:
                args_str += ", "
            operand, arg_ir = self.gen_expression(arg)
            ir += arg_ir
            args_str += f"{self.llvm_type(arg.typ)} {operand}"

        return ir, args_str

    @staticmethod
    def llvm_type(typ) -> str:
        if typ is types.Integer64 or isinstance(typ, types.Integer64):
            return "i64"
        if typ is types.Float64 or isinstance(typ, types.Float64):
            return "double"
        if typ is types.Void or isinstance(typ, types.Void):
            return "void"
        print(f"Cannot convert type {typ} to llvm ir (was the AST validated?)")
        sys.exit(1)

    @staticmethod
    def llvm_double(value: float) -> str:
        bits = struct.unpack("<Q", struct.pack("<d", float(value)))[0]
        return f"0x{bits:016X}"

    def new_temp(self) -> str:
        name = f"%t{self.temp_counter}"
        self.temp_counter += 1
        return name

    def gen_expression(self, node: types.Expression) -> tuple[str, str]:
        match node:
            case types.BinaryExpression():
                left, left_ir = self.gen_expression(node.left)
                right, right_ir = self.gen_expression(node.right)
                ir = left_ir + right_ir

                if node.typ is types.Integer64:
                    inst = self.make_i64_op(node.op)
                elif node.typ is types.Float64:
                    inst = self.make_f64_op(node.op)
                else:
                    print(f"Binary '{node.op}' on unsupported type {node.typ}")
                    sys.exit(1)

                tmp = self.new_temp()
                ir += f"\n{tmp} = {inst} {self.llvm_type(node.typ)} {left}, {right}"
                return tmp, ir

            case types.UnaryExpression():
                operand, ir = self.gen_expression(node.expr)
                if node.sign == "+":
                    return operand, ir

                tmp = self.new_temp()
                if node.typ is types.Float64:
                    ir += f"\n{tmp} = fneg double {operand}"
                else:
                    ir += f"\n{tmp} = sub i64 0, {operand}"
                return tmp, ir

            case types.PrimaryExpression():
                match node.value:
                    case types.Integer64():
                        return str(node.value.value), ""
                    case types.Float64():
                        return self.llvm_double(node.value.value), ""
                    case types.VariableRef():
                        if node.value.mutable:
                            tmp = self.new_temp()
                            match node.value.typ:
                                case types.Integer64:
                                    return tmp, f"\n{tmp} = load i64, i64* %{node.value.irname}, align 8"
                                case types.Float64:
                                    return tmp, f"\n{tmp} = load double, double* %{node.value.irname}, align 8"
                                case _:
                                    print(f"Type {self.value.typ} is unimplemented for mutable VariableRef")
                                    sys.exit(1)
                        else:
                            return f"%{node.value.irname}", ""
                    case types.FunctionCall():
                        args_ir, args_str = self.get_function_args_llvm(node.value)
                        tmp = self.new_temp()
                        ret_ty = self.llvm_type(node.typ)
                        ir = (
                            args_ir
                            + f"\n{tmp} = call {ret_ty} @{node.value.irname}({args_str})"
                        )
                        return tmp, ir
                    case _:
                        print(
                            f"gen_expression() for PrimaryExpression for {type(node.value)}"
                        )
                        sys.exit(1)
            case _:
                print(f"Invalid expression types found during codegen: {node}")
                sys.exit(1)
