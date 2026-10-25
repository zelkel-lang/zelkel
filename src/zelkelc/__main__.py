from src.zelkelc.lexer.tokenizer import lex
from src.zelkelc.ast.parser import Parser
from src.zelkelc.validator.validator import Validator
from src.zelkelc.codegen.codegen import Codegen

import rich

source = """
class String {
    val value: i64
    
    fn test() -> void {
        return
    }
    
}

fn main() -> void {
    val a: i64 = 1
    val test: i64 = a + 1
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