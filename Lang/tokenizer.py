from enum import StrEnum
from dataclasses import dataclass
import re


class TokenType(StrEnum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    OPERATOR = "OPERATOR"

    LITERAL = "LITERAL"
    DECORATOR = "DECORATOR"

    LPAREN = "LPAREN"
    RPAREN = "RPAREN"

    LBRACE = "LBRACE"
    RBRACE = "RBRACE"

    SYMBOL = "SYMBOL"

    END = "END"
    SKIP = "SKIP"
    MISMATCH = "MISMATCH"
    NEWFILE = "NEWFILE"

    EOF = "EOF"


token_specification = [
    ('NUMBER', r'\d+(\.\d*)?'),
    #('STRING', r'"[^"]*"'),
    ('STRING', r'("[^"]*"|\'[^\']*\')'),
    ('DECORATOR', r'@[A-Za-z_]\w*'),
    ('IDENTIFIER', r'[A-Za-z_]\w*'),
    (TokenType.OPERATOR, r'[+\-*/><=]'),
    (TokenType.LBRACE, r'\{'),
    (TokenType.RBRACE, r'\}'),
    (TokenType.LPAREN, r'\('),
    (TokenType.RPAREN, r'\)'),
    (TokenType.SYMBOL, r'[:,]'),
    ('NEWLINE', r'\n'),
    ('SKIP', r'[ \t]+'),
    ('MISMATCH', r'.'),
]

tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)

keywords = [
    "let", "procedure", "sprite"
]


@dataclass
class Token:
    token_type: TokenType
    value: str
    line: int
    column: int

    def __str__(self):
        return f"({self.token_type}, \"{self.value}\")"

    def __repr__(self):
        return self.__str__()


def tokenize(text: str) -> list[Token]:
    tokens = []
    line_num = 1
    line_start = 0

    for mo in re.finditer(tok_regex, text):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start

        match kind:
            case "NUMBER":
                tokens.append(Token(TokenType.LITERAL, value, line_num, column))
            case "STRING":
                # Strip the quotes off the value for the AST
                tokens.append(Token(TokenType.LITERAL, value.strip('"').strip("'"), line_num, column))
            case "IDENTIFIER":
                token_type = TokenType.IDENTIFIER
                if value in keywords:
                    token_type = TokenType.KEYWORD
                tokens.append(Token(token_type, value, line_num, column))
            case "DECORATOR":
                tokens.append(Token(TokenType.DECORATOR, value, line_num, column))
            case "NEWLINE":
                tokens.append(Token(TokenType.END, "\n", line_num, column))
                line_start = mo.end()
                line_num += 1
            case "SKIP":
                continue
            case "MISMATCH":
                raise SyntaxError(f"Unexpected character '{value}' at line {line_num}, column {column}")
            case _:
                token_type = TokenType[kind]
                tokens.append(Token(token_type, value, line_num, column))

    tokens.append(Token(TokenType.EOF, "", line_num, len(text) - line_start))
    return tokens


def run_test():
    code = """
        sprite Duck {
            procedure main() {
                say("hi?")
            }
        }
    """
    print(tokenize('"Hello"'))


if __name__ == "__main__":
    run_test()
