import unittest
from Lang.parser import Parser
from Lang.mangling import get_unique_mangle_id_generator


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

    def test_mangle(self):
        mangle_generator = get_unique_mangle_id_generator()

        for i in range(3000):
            print(next(mangle_generator))


if __name__ == '__main__':
    unittest.main()
