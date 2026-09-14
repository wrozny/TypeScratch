import unittest
from Lang.parser import Parser


class ParserTestCases(unittest.TestCase):
    def test_sprite_declaration(self):
        text = """
            sprite Duck {
                @start {
                   
                }
            }
        """

        lang_parser = Parser()
        lang_parser.feed_text(text)

        my_ast = lang_parser.build_ast()

        print(my_ast)


if __name__ == '__main__':
    unittest.main()
