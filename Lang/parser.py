import os

from .tokenizer import Token, TokenType, tokenize
from .scratch_ast import (
    ASTNode, EntryPoint, FunctionCall, MathOperation, ProcedureDefinition,
    Reporter, ScratchOperator, SpriteDefinition, UnaryOperation, Value,
    VariableDeclaration, VariableReference, VariableSet,
)


class ParseException(Exception):
    """Defines errors caused by unsupported parser features or invalid parser usage."""


class Parser:
    """Builds syntax trees using a cursor without removing tokens from the input."""

    _BINARY_OPERATORS = {
        "or": (1, ScratchOperator.OR),
        "and": (2, ScratchOperator.AND),
        "==": (3, ScratchOperator.EQUAL),
        "!=": (3, ScratchOperator.NOT_EQUAL),
        "<": (4, ScratchOperator.LESS_THAN),
        ">": (4, ScratchOperator.GREATER_THAN),
        "<=": (4, ScratchOperator.LESS_EQUAL),
        ">=": (4, ScratchOperator.GREATER_EQUAL),
        "+": (5, ScratchOperator.ADD),
        "-": (5, ScratchOperator.SUBTRACT),
        "*": (6, ScratchOperator.MULTIPLY),
        "/": (6, ScratchOperator.DIVIDE),
        "%": (6, ScratchOperator.MODULO),
    }
    _ASSIGNMENT_OPERATORS = {"=", "+=", "-=", "*=", "/=", "%="}

    def __init__(self):
        """Initializes the token cursor, source location and parser context."""
        self.current_token_index = 0
        self.tokens: list[Token] = []
        self.tokens_count = 0
        self.current_file = None
        self.scope = []
        self._parenthesis_depth = 0

    def feed_text(self, text: str, add_new_file_token: bool = True):
        """
        Appends source text to the parser input.
        :param text: Source text to tokenize
        :param add_new_file_token: Whether to insert a source boundary marker
        """
        if add_new_file_token:
            self.feed_tokens([Token(TokenType.NEWFILE, "", 0, 0)])
        self.feed_tokens(tokenize(text))

    def feed_file(self, path: str):
        """
        Appends a source file to the parser input.
        :param path: Path of the file to parse
        """
        if not os.path.isfile(path):
            raise ParseException(f"File feeding to parser failed, path {path} isn't a real path!")
        with open(path, encoding="utf-8") as source:
            self.feed_tokens([Token(TokenType.NEWFILE, path, 0, 0)])
            self.feed_text(source.read(), add_new_file_token=False)

    def feed_tokens(self, tokens: list[Token]):
        """
        Appends a copy of the provided tokens without taking ownership of the list.
        :param tokens: Tokens to append
        """
        self.tokens.extend(tokens)
        self.tokens_count = len(self.tokens)

    def current_token(self) -> Token | None:
        """Returns the token at the cursor, or None after the input ends."""
        if self.current_token_index < self.tokens_count:
            return self.tokens[self.current_token_index]
        return None

    def next_token(self) -> Token | None:
        """Advances the cursor by one token and returns the new current token."""
        self.current_token_index = min(self.current_token_index + 1, self.tokens_count)
        return self.current_token()

    def expect_current_token(self, token_type: TokenType | None = None,
                             token_value: str | None = None) -> Token:
        """
        Validates the current token and raises a positioned SyntaxError on mismatch.
        :param token_type: Required token type, or None for any type
        :param token_value: Required token value, or None for any value
        :return: The matching current token
        """
        token = self.current_token()
        if token is None:
            self._syntax_error(f"Expected ({token_type}, {token_value}), got end of input")
        if ((token_type is not None and token.token_type != token_type)
                or (token_value is not None and token.value != token_value)):
            self._syntax_error(f"Expected ({token_type}, {token_value}), got {token}", token)
        return token

    def expect_current_token_one_of(self, *expected: tuple[TokenType | None, str | None]) -> Token:
        """
        Validates that the current token matches one of the provided pairs.
        :param expected: Allowed token type and value pairs; None matches any value
        :return: The matching current token
        """
        token = self.expect_current_token()
        for token_type, token_value in expected:
            if ((token_type is None or token.token_type == token_type)
                    and (token_value is None or token.value == token_value)):
                return token
        self._syntax_error(f"Expected one of {expected}, got {token}", token)

    def _syntax_error(self, message: str, token: Token | None = None):
        """Raises a syntax error including the available file, line and column."""
        token = token or self.current_token()
        if token is None and self.tokens:
            token = self.tokens[-1]
        location = f"line: {token.line}, column: {token.column}" if token else "end of input"
        if self.current_file:
            location = f"file: {self.current_file}, {location}"
        raise SyntaxError(f"{message}, {location}")

    def _create_subparser(self, starting_tokens: list[Token]) -> "Parser":
        """
        Creates a parser for a block with an independent cursor and copied context.
        :param starting_tokens: Tokens belonging to the nested block
        :return: The nested parser
        """
        parser = Parser()
        parser.scope = self.scope.copy()
        parser.current_file = self.current_file
        parser.feed_tokens(starting_tokens)
        return parser

    def _consume_content(self, opening_token_type: TokenType,
                         closing_token_type: TokenType) -> list[Token]:
        """
        Copies a balanced block's contents and advances past its closing token.
        :param opening_token_type: Token type opening the block
        :param closing_token_type: Token type closing the block
        :return: Interior tokens, leaving the original token list unchanged
        """
        opening = self.expect_current_token(opening_token_type)
        self.next_token()
        start = self.current_token_index
        depth = 1
        while (token := self.current_token()) is not None:
            if token.token_type in (TokenType.EOF, TokenType.NEWFILE):
                self._syntax_error(f"Missing closing token {closing_token_type}", opening)
            if token.token_type == opening_token_type:
                depth += 1
            elif token.token_type == closing_token_type:
                depth -= 1
                if depth == 0:
                    contents = self.tokens[start:self.current_token_index]
                    self.next_token()
                    return contents
            self.next_token()
        self._syntax_error(f"Missing closing token {closing_token_type}", opening)

    def _consume_braces(self) -> list[Token]:
        """Returns a brace block's contents and advances past its closing brace."""
        return self._consume_content(TokenType.LBRACE, TokenType.RBRACE)

    def _parse_sprite(self) -> SpriteDefinition:
        """Parses a global sprite declaration and retains its complete ordered body."""
        token = self.expect_current_token(TokenType.KEYWORD, "sprite")
        if self.scope:
            self._syntax_error("Sprite has to be declared in global scope", token)
        self.next_token()
        name = self.expect_current_token(TokenType.IDENTIFIER).value
        self.next_token()
        self._skip_newlines()
        parser = self._create_subparser(self._consume_braces())
        parser.scope.extend(["Sprite", name])
        body = parser.build_ast()
        return SpriteDefinition(
            line=token.line, column=token.column, name=name,
            procedures=[node for node in body if isinstance(node, ProcedureDefinition)],
            entry_points=[node for node in body
                          if isinstance(node, EntryPoint) and not isinstance(node, ProcedureDefinition)],
            variable_declarations=[node for node in body if isinstance(node, VariableDeclaration)],
            body=body,
        )

    def _parse_decorator(self) -> EntryPoint:
        """Parses an entry point with a brace body, preserving declarations and calls."""
        token = self.expect_current_token(TokenType.DECORATOR)
        instruction_name = {"@start": "__whenflagclicked"}.get(token.value)
        if instruction_name is None:
            self._syntax_error(f"Invalid entry point definition {token.value}", token)
        self.next_token()
        self._skip_newlines()
        if self.current_token() and self.current_token().token_type == TokenType.LPAREN:
            raise ParseException("Decorator arguments are not yet implemented!")
        parser = self._create_subparser(self._consume_braces())
        parser.scope.append("EntryPoint")
        return EntryPoint(line=token.line, column=token.column,
                          instruction_name=instruction_name, arguments=[], body=parser.build_ast())

    def _parse_keyword(self) -> list[ASTNode]:
        """Dispatches supported keyword declarations and returns their AST nodes."""
        token = self.expect_current_token(TokenType.KEYWORD)
        if token.value == "sprite":
            return [self._parse_sprite()]
        if token.value == "let":
            return self._parse_variable_declaration()
        raise ParseException(f"Keyword {token.value} is not implemented yet inside _parse_keyword()")

    def _parse_variable_declaration(self) -> list[ASTNode]:
        """Parses a variable declaration and an optional initializer assignment."""
        token = self.expect_current_token(TokenType.KEYWORD, "let")
        self.next_token()
        name = self.expect_current_token(TokenType.IDENTIFIER).value
        self.next_token()
        nodes: list[ASTNode] = [VariableDeclaration(
            line=token.line, column=token.column, variable_name=name,
            is_global=not self.scope,
        )]
        current = self.current_token()
        if current and current.token_type == TokenType.OPERATOR and current.value == "=":
            self.next_token()
            value = self._parse_expression()
            nodes.append(VariableSet(line=token.line, column=token.column,
                                     arguments=[], variable_name=name, new_value=value))
        self._expect_statement_end()
        return nodes

    def _parse_identifier(self, force_no_setters: bool = False) -> ASTNode:
        """
        Parses an assignment or an expression starting with an identifier.
        :param force_no_setters: Whether to forbid parsing an assignment
        :return: An assignment, reference, call or binary expression
        """
        token = self.expect_current_token(TokenType.IDENTIFIER)
        following_index = self.current_token_index + 1
        following = self.tokens[following_index] if following_index < self.tokens_count else None
        if (not force_no_setters and following is not None
                and following.token_type == TokenType.OPERATOR
                and following.value in self._ASSIGNMENT_OPERATORS):
            self.next_token()
            operator = self.current_token()
            self.next_token()
            value = self._parse_expression()
            if operator.value != "=":
                value = MathOperation(
                    line=operator.line, column=operator.column,
                    operator=self._BINARY_OPERATORS[operator.value[:-1]][1],
                    left_value=VariableReference(line=token.line, column=token.column,
                                                 variable_name=token.value),
                    right_value=value,
                )
            node = VariableSet(line=token.line, column=token.column,
                               arguments=[], variable_name=token.value, new_value=value)
        else:
            node = self._parse_expression()
        if not force_no_setters:
            self._expect_statement_end()
        return node

    def _skip_newlines(self):
        """Advances over line breaks without accepting semicolons or file boundaries."""
        while (token := self.current_token()) is not None:
            if token.token_type != TokenType.END or token.value != "\n":
                return
            self.next_token()

    def _skip_expression_newlines(self):
        """Allows multiline expressions only inside parentheses or argument lists."""
        if self._parenthesis_depth:
            self._skip_newlines()

    def _parse_expression(self, minimum_precedence: int = 1) -> Reporter:
        """
        Parses left associative binary operators using precedence climbing.
        :param minimum_precedence: Lowest operator precedence accepted in this subtree
        :return: The expression tree, leaving its delimiter at the cursor
        """
        left = self._parse_unary()
        while True:
            self._skip_expression_newlines()
            token = self.current_token()
            operator = self._BINARY_OPERATORS.get(token.value) if token else None
            if (token is None or token.token_type != TokenType.OPERATOR
                    or operator is None or operator[0] < minimum_precedence):
                return left
            self.next_token()
            right = self._parse_expression(operator[0] + 1)
            left = MathOperation(line=token.line, column=token.column,
                                 operator=operator[1], left_value=left, right_value=right)

    def _parse_unary(self) -> Reporter:
        """Parses prefix signs and logical negation before binary operators."""
        self._skip_expression_newlines()
        token = self.current_token()
        if token and token.token_type == TokenType.OPERATOR and token.value in ("-", "+", "!", "not"):
            self.next_token()
            return UnaryOperation(line=token.line, column=token.column,
                                  operator=token.value, operand=self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self) -> Reporter:
        """Parses a value, variable reference, named function call or grouped expression."""
        self._skip_expression_newlines()
        token = self.expect_current_token()
        if token.token_type == TokenType.LITERAL:
            self.next_token()
            return Value(line=token.line, column=token.column, value=token.value)
        if token.token_type == TokenType.IDENTIFIER:
            self.next_token()
            if self.current_token() and self.current_token().token_type == TokenType.LPAREN:
                return self._parse_call(token)
            return VariableReference(line=token.line, column=token.column, variable_name=token.value)
        if token.token_type == TokenType.LPAREN:
            self.next_token()
            self._parenthesis_depth += 1
            try:
                expression = self._parse_expression()
                self.expect_current_token(TokenType.RPAREN)
                self.next_token()
                return expression
            finally:
                self._parenthesis_depth -= 1
        self._syntax_error(f"Expected an expression, got {token}", token)

    def _parse_call(self, name_token: Token) -> FunctionCall:
        """
        Parses comma separated expression arguments for a named call.
        :param name_token: Identifier naming the called function
        :return: A call expression with its argument trees
        """
        self.expect_current_token(TokenType.LPAREN)
        self.next_token()
        self._parenthesis_depth += 1
        arguments = []
        try:
            self._skip_expression_newlines()
            if self.current_token() and self.current_token().token_type != TokenType.RPAREN:
                while True:
                    arguments.append(self._parse_expression())
                    token = self.current_token()
                    if token and token.token_type == TokenType.SYMBOL and token.value == ",":
                        self.next_token()
                    else:
                        break
            self.expect_current_token(TokenType.RPAREN)
            self.next_token()
        finally:
            self._parenthesis_depth -= 1
        return FunctionCall(line=name_token.line, column=name_token.column,
                            function_name=name_token.value, arguments=arguments)

    def _expect_statement_end(self):
        """Rejects leftover expression tokens unless a statement or input boundary follows."""
        token = self.current_token()
        if token is not None and token.token_type not in (TokenType.END, TokenType.EOF, TokenType.NEWFILE):
            self._syntax_error(f"Expected end of statement, got {token}", token)

    def build_ast(self) -> list[ASTNode]:
        """Parses all supplied tokens into a complete list of AST nodes."""
        nodes = []
        while (token := self.current_token()) is not None:
            if token.token_type in (TokenType.END, TokenType.EOF, TokenType.NEWFILE):
                if token.token_type == TokenType.NEWFILE:
                    self.current_file = token.value
                self.next_token()
            elif token.token_type == TokenType.KEYWORD:
                nodes.extend(self._parse_keyword())
            elif token.token_type == TokenType.DECORATOR:
                nodes.append(self._parse_decorator())
            elif token.token_type == TokenType.IDENTIFIER:
                nodes.append(self._parse_identifier())
            else:
                nodes.append(self._parse_expression())
                self._expect_statement_end()
        return nodes
