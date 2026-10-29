from src.zelkelc.lexer import token


class TokenError(Exception):
    pass


def lex(source: str) -> list[token.Token]:
    tokens: list[token.Token] = []

    i = 0
    while i < len(source):
        c = source[i]
        if c == "/" and source[i + 1] == "/":
            i += 2
            for _, comment_c in enumerate(source[i:]):
                i += 1
                if comment_c == "\n":
                    break
        elif c.isnumeric():
            i += 1

            isfloat = False
            num = c
            for _, num_c in enumerate(source[i:]):
                if num_c == "_":
                    i += 1
                    continue
                if num_c == ".":
                    isfloat = True
                elif not num_c.isnumeric():
                    break
                i += 1
                num += num_c

            if isfloat:
                tokens.append(token.Float(float(num)))
            else:
                tokens.append(token.Integer(int(num)))
        elif c.isalpha() or c == "_":
            i += 1

            identifier = c
            for _, identifier_c in enumerate(source[i:]):
                if not (identifier_c.isalnum() or identifier_c == "_"):
                    break
                i += 1
                identifier += identifier_c
            tokens.append(token.Identifier(identifier))
        elif c == '"':
            i += 1

            string = ""
            for _, string_c in enumerate(source[i:]):
                if string_c == '"':
                    break
                i += 1
                string += string_c
            if i >= len(source) or source[i] != '"':
                raise TokenError("No '\"' to close string")
            i += 1
            tokens.append(token.String(string))
        elif c == "#" and i + 1 < len(source) and source[i + 1] == '"':
            i += 2

            string = ""
            while i < len(source):
                if source[i] == '"' and i + 1 < len(source) and source[i + 1] == "#":
                    i += 2
                    tokens.append(token.String(string))
                    break
                string += source[i]
                i += 1
            else:
                raise TokenError("No '\"#' to close string")
        elif c == "-" and source[i + 1] == ">":
            tokens.append(token.Arrow())
            i += 2
        elif c == "+" and source[i + 1] == "=":
            tokens.append(token.Assigner("+="))
            i += 2
        elif c == "-" and source[i + 1] == "=":
            tokens.append(token.Assigner("-="))
            i += 2
        elif c == "*" and source[i + 1] == "=":
            tokens.append(token.Assigner("*="))
            i += 2
        elif c == "/" and source[i + 1] == "=":
            tokens.append(token.Assigner("/="))
            i += 2
        elif c == "<" and source[i + 1] == "=":
            tokens.append(token.Operator("<="))
            i += 2
        elif c == ">" and source[i + 1] == "=":
            tokens.append(token.Operator(">="))
            i += 2
        elif c == "|" and source[i + 1] == "|":
            tokens.append(token.Operator("||"))
            i += 2
        elif c == "&" and source[i + 1] == "&":
            tokens.append(token.Operator("&&"))
            i += 2
        elif c == "=" and source[i + 1] == "=":
            tokens.append(token.Operator("=="))
            i += 2
        elif c == "!" and source[i + 1] == "=":
            tokens.append(token.Operator("!="))
            i += 2
        else:
            match c:
                case " " | "\n":
                    i += 1
                case "#":
                    tokens.append(token.Pound())
                    i += 1
                case "(":
                    tokens.append(token.LParen())
                    i += 1
                case ")":
                    tokens.append(token.RParen())
                    i += 1
                case "{":
                    tokens.append(token.LBrace())
                    i += 1
                case "}":
                    tokens.append(token.RBrace())
                    i += 1
                case ".":
                    tokens.append(token.Period())
                    i += 1
                case ",":
                    tokens.append(token.Comma())
                    i += 1
                case ":":
                    tokens.append(token.Colon())
                    i += 1
                case "=":
                    tokens.append(token.Assigner("="))
                    i += 1
                case "+":
                    tokens.append(token.Operator("+"))
                    i += 1
                case "-":
                    tokens.append(token.Operator("-"))
                    i += 1
                case "*":
                    tokens.append(token.Operator("*"))
                    i += 1
                case "/":
                    tokens.append(token.Operator("/"))
                    i += 1
                case "%":
                    tokens.append(token.Operator("%"))
                    i += 1
                case "$":
                    tokens.append(token.Dollar())
                    i += 1
                case _:
                    raise TokenError(
                        f"Unknown character found during lexing: '{c}' at {i}"
                    )

    return tokens
