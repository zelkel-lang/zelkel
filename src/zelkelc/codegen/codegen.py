import src.zelkelc.ast.types as types

class IRTable:
    structs: str
    struct_functions: str
    global_functions: str
    
    def __init__(self):
        self.structs = ""
        self.struct_functions = ""
        self.global_functions = ""

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
                case _:
                    print(f"Invalid node found during codegen {type(node)}")
                    exit(1)
        
        return self.ir.structs + "\n" + self.ir.struct_functions + "\n" + self.ir.global_functions
    
    def gen_struct_declaration(self, node: types.StructDeclaration):
        members_str = ""
        for i, m in enumerate(node.members):
            members_str += f"{", " if i != 0 else ""}{m.typ.to_llvm()}"

        self.ir.structs += f"\n%{node.irname} = type " + "{ " + members_str + " }"

    def gen_class_declaration(self, node: types.ClassDeclaration):
        members_str = ""
        for i, m in enumerate(node.members):
            members_str += f"{", " if i != 0 else ""}{m.typ.to_llvm()}"
        
        self.ir.structs += f"\n%{node.irname} = type " + "{ " + members_str + " }"
        
        for func in node.methods:
            self.ir.struct_functions += self.gen_function_declaration(func)
    
    def gen_function_declaration(self, node: types.FunctionDeclaration) -> str:
        args_str = ""
        for i, (name, typ) in enumerate(node.args.items()):
            args_str += f"{", " if i != 0 else ""}{typ.to_llvm()} %{name}"
            
        ir = f"\ndefine {str(node.typ.to_llvm())} @{node.irname}({args_str}) " + "{"
        ir += "\nentry:"
        
        for child_node in node.body:
            match child_node:
                case types.ValueDeclaration():
                    ir += self.gen_value_declaration(child_node)
                case _:
                    continue
        
        return ir + "\n}"
    
    def gen_value_declaration(self, node: types.ValueDeclaration) -> str:
        ir = ""
        
        count, expr = self.gen_expression(node.expr)
        ir += expr
        
        match node.typ:
            case types.Integer64:
                if node.mutable == True:
                    ir += f"\n%{node.irname} = alloca i64, align 8" # TODO: this would only work for i64s, just testing
                    ir += f"\nstore i64 %{count}, i64* %{node.irname}, align 8"
                else:
                    ir += f"\n%{node.irname} = add i64 %{count}, 0"
            case _:
                print(f"gen_value_declaration() for {type(node.typ)} is unimplemented")
                exit(1)
            
        return ir
    
    def gen_expression(self, node: types.Expression) -> tuple[str, str]:
        ir = ""
        
        match type(node):
            case types.BinaryExpression:
                left_irname, left = self.gen_expression(node.left)
                right_irname, right = self.gen_expression(node.right)
                
                ir += left + right
                
                op = ""
                match node.op:
                    case '+':
                        op = "add"
                    case '-':
                        op = "sub"
                    case '*':
                        op = "mul"
                    case '/':
                        print("gen_expression() for BinaryExpression for operator '/' is unimplemented")
                        exit(1)
                    case _:
                        print(f"gen_expression() for BinaryExpression for operator '{node.op}' is unimplemented")
                        exit(1)
                        
                match node.left.typ:
                    case types.Integer64:
                        ir += f"\n%{self.temp_counter} = {op} i64 %{left_irname}, %{right_irname}"
                        self.temp_counter += 1
                    case types.VariableRef:
                        match node.left.value.typ:
                            case types.Integer64:
                                ir += f"\n%{self.temp_counter} = {op} i64 %{left_irname}, %{right_irname}"
                                self.temp_counter += 1
                            case _:
                                print(f"gen_expression() for BinaryExpression left operand variable type '{node.left.value.typ}' is unimplemented")
                    case _:
                       print(f"gen_expression() for BinaryExpression for {node.left.typ}")
                       exit(1)
            case types.UnaryExpression:
                print("gen_expression() for UnaryExpression unimplemented")
                exit(1)
            case types.PrimaryExpression:
                match type(node.value):
                    case types.Integer64:
                        ir += f"\n%{self.temp_counter} = add i64 {node.value.value}, 0"
                        self.temp_counter += 1
                    case types.VariableRef:
                        return node.value.irname, ir
                    case _:
                        print(f"gen_expression() for PrimaryExpression for {type(node.value)}")
                        exit(1)
            case _:
                print(f"Invalid expression types found during codegen: {node}")
                exit(1)

        return str(self.temp_counter - 1), ir