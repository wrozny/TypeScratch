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

    def next_token(self) -> Token | None:
        """
        Returns the next token in tokens list
        :return: Next token
        """

        self.current_token_index += 1
        if self.current_token_index > self.tokens_count:
            self.current_token_index = self.tokens_count
        return self.current_token()

    def expect_tokens(self, possible_tokens: list[TokenType]):
        """
        Acts as a next_token but throws an exception when
        :param token_type:
        :param token_value:
        :return:
        """
        next_token = self.next_token()
        if next_token is None:
            raise ParseException("")

    def build_ast(self):
        """
        Parses the provided tokens and constructs an abstract syntax tree
        :return:
        """
        pass
