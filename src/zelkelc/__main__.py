from src.zelkelc.lexer.tokenizer import lex
from src.zelkelc.ast.parser import Parser
from src.zelkelc.validator.validator import Validator
from src.zelkelc.codegen.codegen import Codegen

import rich

source = """
#llvm(
    #"@int.fmt = private unnamed_addr constant [5 x i8] c"%ld\0A\00""#
)

#llvm(
    #"declare i32 @printf(ptr, ...)"#
)

fn main() -> void {
    val test: i64 = 2 + 2*3
    
    #llvm(
        "%call = call i32 (ptr, ...) @printf(ptr @int.fmt, i64 %v_27_test)"
    )
    
    return
}
"""

if __name__ == "__main__":
    tokens = lex(source)
    print(tokens)
    parser = Parser(tokens, 0)
    ast = parser.parse()
    rich.print(ast)
    
    Validator(ast)
    
    codegen = Codegen(ast)
    ir = codegen.generate()
    print(ir)