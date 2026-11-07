import unittest

from Lang.ast_resolution import NameResolver
from Lang.parser import Parser


class ASTResolutionTestCases(unittest.TestCase):
    def test_name_resolution(self):
        code = """
            let x = 10
            sprite Duck {
                let x = 20
                if x > 10 {
                    let x = 65 
                }
                
                let some = "Hi!"
            }
        """
        parser = Parser()
        parser.feed_text(code)
        ast = parser.build_ast()
        name_resolver = NameResolver(ast)
        name_resolver.resolve()

        local_variables_target = {"Duck": {"2-x", "3-x", "4-some"}}
        self.assertEqual(name_resolver.local_variables, local_variables_target)

        global_variables_target = {"1-x"}
        self.assertEqual(name_resolver.global_variables, global_variables_target)


if __name__ == '__main__':
    unittest.main()
