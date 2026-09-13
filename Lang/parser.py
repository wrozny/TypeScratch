from .tokenizer import *
from .scratch_ast import *
from .mangling import get_unique_mangle_id_generator
import os

UNIQUE_ID_GENERATOR = get_unique_mangle_id_generator()


class ParseException(Exception):
    """
        Exception thrown in Parser class
    """
    pass


class Parser:
    def __init__(self):
        self.current_token_index = 0
        self.tokens = []
        self.tokens_count = len(self.tokens)
        self.current_file = None
        self.scope = []

    def feed_text(self, text: str, add_new_file_token: bool = True):
        """
        Feeds the text to be parsed
        :param text: Text to be parsed
        :param add_new_file_token: Tells whether to add a token saying where new feed_text call happened
        """
        if add_new_file_token:
            self.tokens.append(Token(TokenType.NEWFILE, "", 0, 0))

        for token in tokenize(text):
            self.tokens.append(token)
        self.tokens_count = len(self.tokens)

    def feed_file(self, path: str):
        """
        Feeds the text from a file to be parsed
        :param path: Path of the file to be parsed
        """
        if os.path.isfile(path):
            with open(file=path, encoding="utf-8", mode="r") as source:
                self.tokens.append(Token(TokenType.NEWFILE, path, 0, 0))
                self.feed_text(source.read(), add_new_file_token=False)
        else:
            raise ParseException(f"File feeding to parser failed, path {path} isn't a real path!")

    def feed_tokens(self, tokens: list[Token]):
        """
        Feeds the provided tokens by appending them to tokens list
        :param tokens: Tokens to feed
        """
        if self.tokens_count == 0:
            self.tokens = tokens
        else:
            for token in tokens:
                self.tokens.append(token)

        self.tokens_count = len(self.tokens)

    def current_token(self) -> Token | None:
        """
        Returns current token being parsed
        :return: Current token being parsed
        """
        if self.current_token_index < self.tokens_count:
            return self.tokens[self.current_token_index]

        return None

    def pop_current_token(self) -> Token | None:
        """
        Removes the current token from tokens list and returns it, automatically moves forward because of it
        :return: Current token
        """
        if self.current_token_index < self.tokens_count:
            self.tokens_count -= 1
            return self.tokens.pop(self.current_token_index)

        return None

    def next_token(self) -> Token | None:
        """
        Returns the next token in tokens list
        :return: Next token
        """
        self.current_token_index += 1
        if self.current_token_index > self.tokens_count:
            self.current_token_index = self.tokens_count
        return self.current_token()

    def expect_current_token(self, token_type: TokenType | None = None, token_value: str | None = None) -> Token:
        """
        Throws a SyntaxError when current token type or token value doesn't match the arguments.
        token_type and token_value are None by default which means that they aren't required.
        This method ensures that current token exists, otherwise throws ParseException.
        :param token_type: token type to match
        :param token_value: token value to match
        :return: Current token
        """
        current_token = self.current_token()
        if current_token is None:
            raise ParseException(f"Expected next token is a None! Expected: ({token_type}, {token_value})")

        token_type_mismatch = token_type is not None and current_token.token_type != token_type
        token_value_mismatch = token_value is not None and current_token.value != token_value

        if token_type_mismatch or token_value_mismatch:
            raise SyntaxError(
                f"Expected {' '.join([token_type, token_value])} "
                f"got {' '.join([current_token.token_type, current_token.value])} instead, "
                f"line: {current_token.line}, column: {current_token.column}"
            )

        return current_token

    def expect_current_token_one_of(self, *expected: tuple[TokenType | None, str | None]) -> Token:
        """
        Ensures that the current token matches at least one of the provided
        (token_type, token_value) pairs.

        None means that the corresponding field isn't required to match.
        Throws ParseException if there is no current token.
        Throws SyntaxError if the current token matches none of the expected pairs.

        :param expected: Expected (token_type, token_value) pairs.
        :return: Current token
        """
        current_token = self.current_token()

        if current_token is None:
            raise ParseException(f"Expected one of: {expected}, got None!")

        for token_type, token_value in expected:
            token_type_mismatch = token_type is not None and current_token.token_type != token_type
            token_value_mismatch = token_value is not None and current_token.value != token_value

            if not token_type_mismatch and not token_value_mismatch:
                return current_token

        raise SyntaxError(
            f"Expected one of {expected}, "
            f"got ({current_token.token_type}, {current_token.value}) instead, "
            f"line: {current_token.line}, column: {current_token.column}"
        )

    def create_subparser(self, starting_tokens: list[Token] | None = None) -> "Parser":
        """
        Creates a new Parser object that saves
        :return:
        """

        new_parser = Parser()
        new_parser.scope = self.scope.copy()
        new_parser.current_file = self.current_file

        if starting_tokens is not None:
            new_parser.feed_tokens(starting_tokens)

        return new_parser

    def _parse_sprite(self):
        """
        Parses the sprite definition
        :return:
        """

        if len(self.scope) > 0:
            raise SyntaxError(
                f"Sprite has to be declared in global scope! line: {self.current_token().line} column: {self.current_token().column}")

        self.scope.append("Sprite")

        sprite_token = self.current_token()
        starting_line = sprite_token.line
        starting_column = sprite_token.column

        self.next_token()
        self.expect_current_token(token_type=TokenType.IDENTIFIER)
        sprite_name = self.current_token().value

        self.scope.append(sprite_name)

        self.next_token()
        sprite_definition_tokens = self._consume_braces()

        internal_parser = self.create_subparser(sprite_definition_tokens)
        internal_parser.scope.append("Sprite")
        internal_parser.scope.append(sprite_name)

        internal_nodes = internal_parser.build_ast()

        sprite_definition = SpriteDefinition(
            line=starting_line,
            column=starting_column,
            name=sprite_name,
            procedures=[],
            entry_points=[],
            variable_declarations=[]
        )

        for node in internal_nodes:
            if isinstance(node, ProcedureDefinition):
                sprite_definition.procedures.append(node)
            if isinstance(node, VariableDeclaration):
                sprite_definition.variable_declarations.append(node)
            if isinstance(node, EntryPoint):
                sprite_definition.entry_points.append(node)

        return sprite_definition

    def _parse_decorator(self) -> list[EntryPoint | ProcedureDefinition]:
        """
        Method used to parse a decorator (aka entry points)
        for decorator with braces body straight after do the instructions right at entry point
        for decorator with procedure definition after it, call the procedure at entry point start
        :return: List of entry points or procedure definitions
        """

        self.expect_current_token(token_type=TokenType.DECORATOR)
        decorator_value = self.current_token().value

        token_after_decorator = self.next_token()
        self.expect_current_token_one_of(
            (TokenType.LPAREN, None),  # additional decorator arguments
            (TokenType.LBRACE, None),  # entry point directly contains body
            (TokenType.KEYWORD, None)  # might be a procedure definition right after
        )

        if token_after_decorator.token_type == TokenType.LPAREN:
            # !TODO parse parentheses for decorator arguments
            raise ParseException("Decorator arguments are not yet implemented!")

        if token_after_decorator.token_type == TokenType.LBRACE:
            body_tokens = self._consume_braces()
            body_parser = self.create_subparser(body_tokens)
            body_parser.scope.append(next(UNIQUE_ID_GENERATOR))

        # !TODO implement the rest of simple decorator to body logic
        raise ParseException("Decorator parsing is not implemented yet!")

    def _parse_keyword(self):
        """
        Parses the tokens based on the first token which has to be a keyword
        :return:
        """
        self.expect_current_token(token_type=TokenType.KEYWORD)

        current_token = self.current_token()

        resolvers = {
            "sprite": self._parse_sprite
        }

        resolve_parse = resolvers.get(current_token.value)

        if resolve_parse is None:
            raise ParseException(f"Keyword {current_token.value} is not implemented yet inside _parse_keyword()")

        return resolve_parse()

    def _consume_content(self, opening_token_type: TokenType, closing_token_type: TokenType) -> list[Token]:
        """
        Starting at left token pops every token in between from original list until right token and returns it as a list of tokens
        this ensures that inner contents with same left token and right token type will be also caught according to depth
        :param opening_token_type: Token type that opens contents
        :param closing_token_type: Token type that ends contents
        :return: List of tokens in between
        """

        if self.current_token().token_type != opening_token_type:
            raise ParseException(
                f"Can't start consuming content if starting token {self.current_token()} isn't of type {opening_token_type}!")

        self.pop_current_token()

        depth = 1
        consumed_tokens = []

        while depth != 0:
            next_token = self.pop_current_token()

            if next_token.token_type == TokenType.EOF:
                raise SyntaxError(
                    f"Missing closing token while consuming content, file ended at depth: {depth}, closing token type: {closing_token_type}")

            if next_token.token_type == opening_token_type:
                depth += 1

            if next_token.token_type == closing_token_type:
                depth -= 1

            if depth > 0:
                consumed_tokens.append(next_token)

        return consumed_tokens

    def _consume_braces(self) -> list[Token]:
        """
        Starting at left brace collects every token by popping them until matching right brace
        and returns the list of tokens for further interpretation
        :return:
        """
        return self._consume_content(TokenType.LBRACE, TokenType.RBRACE)

    def _consume_parentheses(self) -> list[Token]:
        """
        Starting at left parenthesis collects every token by popping them until matching right parenthesis
        and returns the list of tokens for further interpretation
        :return:
        """
        return self._consume_content(TokenType.LPAREN, TokenType.RPAREN)

    def build_ast(self) -> list[ASTNode]:
        """
        Parses the provided tokens and constructs an abstract syntax tree
        :return:
        """
        current_token = self.current_token()

        nodes = []

        while current_token is not None:
            self.scope = []
            if current_token.token_type == TokenType.KEYWORD:
                nodes.append(self._parse_keyword())

            current_token = self.next_token()

        return nodes
