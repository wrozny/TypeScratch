from .tokenizer import *
from .scratch_ast import *
import os


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

    def _parse_sprite(self):
        pass

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

    def build_ast(self):
        """
        Parses the provided tokens and constructs an abstract syntax tree
        :return:
        """
        pass
