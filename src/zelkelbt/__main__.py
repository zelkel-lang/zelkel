from src.zelkelbt.config.config import has_config


def print_help():
    print("""
Zelkel Buildtool

Usage: zk [OPTIONS] [COMMAND]

Options:
    -V, --version
""")


if __name__ == "__main__":
    print(has_config())

# tokens = lex(source)
# print(tokens)
# parser = Parser(tokens, 0)
# ast = parser.parse()
# rich.print(ast)

# Validator(ast)

# codegen = Codegen(ast)
# ir = codegen.generate()
# print(ir)
