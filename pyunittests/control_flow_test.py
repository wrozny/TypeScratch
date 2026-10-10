import unittest

from Lang.parser import Parser
from Lang.scratch_ast import (
    Conditional, ForeverLoop, FunctionCall, MathOperation, RepeatLoop,
    ScratchOperator, UnaryOperation, VariableDeclaration, VariableSet, WhileLoop,
)
from Lang.tokenizer import TokenType, tokenize


class ControlFlowTestCases(unittest.TestCase):
    """Verifies control-flow headers, branch binding and nested block parsing."""

    def _parse(self, text):
        """Builds the complete AST for the supplied source."""
        parser = Parser()
        parser.feed_text(text)
        return parser.build_ast()

    def test_control_words_are_reserved(self):
        """Recognizes control keywords without confusing literals or longer names."""
        tokens = tokenize('if else while repeat forever repeat_count "while"')
        self.assertTrue(all(token.token_type == TokenType.KEYWORD for token in tokens[:5]))
        self.assertEqual(tokens[5].token_type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[6].token_type, TokenType.LITERAL)

    def test_if_expression_and_body(self):
        """Keeps precedence, declaration and assignment nodes inside an if statement."""
        node = self._parse('if x + 1 > 2 and check(x) { let y = 3\nsay(y) }')[0]
        self.assertIsInstance(node, Conditional)
        self.assertEqual(node.condition.operator, ScratchOperator.AND)
        comparison = node.condition.left_value
        self.assertEqual(comparison.operator, ScratchOperator.GREATER_THAN)
        self.assertEqual(comparison.left_value.operator, ScratchOperator.ADD)
        self.assertIsInstance(node.condition.right_value, FunctionCall)
        self.assertEqual([type(child) for child in node.body],
                         [VariableDeclaration, VariableSet, FunctionCall])
        self.assertFalse(node.body[0].is_global)
        self.assertIsNone(node.else_body)

    def test_else_body(self):
        """Attaches an unconditional else block to the preceding if."""
        node = self._parse('if x { say("yes") } else { say("no") }')[0]
        self.assertEqual(node.body[0].arguments[0].value, "yes")
        self.assertEqual(node.else_body[0].arguments[0].value, "no")

    def test_empty_else_is_retained(self):
        """Distinguishes an explicit empty else branch from an absent else."""
        node = self._parse("if x {} else {}")[0]
        self.assertEqual(node.else_body, [])

    def test_else_if_chain(self):
        """Stores else if as a conditional within the preceding else branch."""
        node = self._parse("if x == 1 {} else if x == 2 {} else if x == 3 {} else {}")[0]
        second = node.else_body[0]
        third = second.else_body[0]
        self.assertIsInstance(second, Conditional)
        self.assertEqual(second.condition.right_value.value, "2")
        self.assertEqual(third.condition.right_value.value, "3")
        self.assertEqual(third.else_body, [])

    def test_else_binds_to_its_block(self):
        """Keeps inner and outer else branches distinct across nested brace bodies."""
        node = self._parse('if outer { if inner {} else { say("inner") } } '
                           'else { say("outer") }')[0]
        self.assertEqual(node.body[0].else_body[0].arguments[0].value, "inner")
        self.assertEqual(node.else_body[0].arguments[0].value, "outer")

    def test_newlines_around_branches(self):
        """Accepts a brace on the next line and line breaks before else and else if."""
        node = self._parse("if (x >\n 1)\n{}\n\nelse\nif y\n{}\nelse\n{}")[0]
        self.assertEqual(node.condition.operator, ScratchOperator.GREATER_THAN)
        self.assertIsInstance(node.else_body[0], Conditional)
        self.assertEqual(node.else_body[0].else_body, [])

    def test_while_header(self):
        """Preserves the while condition including nested calls and logical negation."""
        node = self._parse("while not done(x) and x < limit(2 + 3) { x += 1 }")[0]
        self.assertIsInstance(node, WhileLoop)
        self.assertEqual(node.condition.operator, ScratchOperator.AND)
        self.assertIsInstance(node.condition.left_value, UnaryOperation)
        self.assertEqual(node.condition.left_value.operand.function_name, "done")
        limit_call = node.condition.right_value.right_value
        self.assertEqual(limit_call.function_name, "limit")
        self.assertEqual(limit_call.arguments[0].operator, ScratchOperator.ADD)
        self.assertIsInstance(node.body[0], VariableSet)

    def test_repeat_count(self):
        """Parses an arbitrary count expression without requiring outer parentheses."""
        node = self._parse("repeat count(2) + 3 * 4 { x += 1 }")[0]
        self.assertIsInstance(node, RepeatLoop)
        self.assertEqual(node.count.operator, ScratchOperator.ADD)
        self.assertEqual(node.count.left_value.function_name, "count")
        self.assertEqual(node.count.right_value.operator, ScratchOperator.MULTIPLY)
        self.assertEqual(len(node.body), 1)

    def test_forever_body(self):
        """Preserves nested loops and conditionals inside an unconditional loop."""
        node = self._parse('forever { repeat 3 { while x { if y { say(y) } } } }')[0]
        self.assertIsInstance(node, ForeverLoop)
        self.assertIsInstance(node.body[0], RepeatLoop)
        self.assertIsInstance(node.body[0].body[0], WhileLoop)
        self.assertIsInstance(node.body[0].body[0].body[0], Conditional)

    def test_control_flow_in_entry_point(self):
        """Retains control nodes and the statements following them in a sprite entry point."""
        sprite = self._parse('sprite Duck { @start { let x = 0\n'
                             'repeat 3 { x += 1 } while x < 5 { x += 1 } '
                             'if x == 5 { say(x) } else { say(0) } '
                             'forever { say(x) } } }')[0]
        self.assertEqual([type(node) for node in sprite.body[0].body],
                         [VariableDeclaration, VariableSet, RepeatLoop, WhileLoop,
                          Conditional, ForeverLoop])

    def test_branch_does_not_consume_next_statement(self):
        """Leaves following statements and source boundaries for the main parser."""
        nodes = self._parse("if x {}\nlet y = 1\nrepeat 2 {}\ny = 3")
        self.assertEqual([type(node) for node in nodes],
                         [Conditional, VariableDeclaration, VariableSet, RepeatLoop, VariableSet])
        parser = Parser()
        parser.feed_text("if x {}")
        parser.feed_text("while y {}")
        self.assertEqual([type(node) for node in parser.build_ast()], [Conditional, WhileLoop])

    def test_block_declarations_are_local(self):
        """Marks declarations in all control bodies as local and restores enclosing context."""
        nodes = self._parse("if x { let y } else { let y }\nwhile x { let y }\n"
                            "repeat 3 { let y }\nforever { let y }\nlet outside")
        bodies = [nodes[0].body, nodes[0].else_body] + [node.body for node in nodes[1:4]]
        self.assertTrue(all(not body[0].is_global for body in bodies))
        self.assertTrue(nodes[-1].is_global)

    def test_control_positions(self):
        """Preserves keyword and expression positions in nested statements."""
        node = self._parse("\nwhile x > 0 {\n  repeat 3 {}\n}")[0]
        self.assertEqual((node.line, node.column), (2, 0))
        self.assertEqual((node.condition.line, node.condition.column), (2, 8))
        self.assertEqual((node.body[0].line, node.body[0].column), (3, 2))

    def test_control_flow_preserves_tokens(self):
        """Leaves source tokens untouched across nested control bodies and else branches."""
        tokens = tokenize("if x { repeat 2 {} }\nelse { forever {} }")
        original = tokens.copy()
        parser = Parser()
        parser.feed_tokens(tokens)
        parser.build_ast()
        self.assertEqual(tokens, original)
        self.assertEqual(parser.tokens, original)
        self.assertEqual(parser.current_token_index, len(original))

    def test_invalid_control_headers(self):
        """Rejects missing expressions, missing braces, stray else and extra header tokens."""
        sources = ["if {}", "while {}", "repeat {}", "if x", "while x",
                   "repeat 3", "forever", "forever 3 {}", "else {}", "else x {}",
                   "if x {} else y {}", "if x {} else if {}", "if x {} else",
                   "if x {} else {} else {}", "if x {} ; else {}",
                   "if x = 1 {}", "repeat 1 2 {}", "while x + {}",
                   "if x; {}", "if x +\n y {}", "if x\n + y {}",
                   "while f(1,) {}", "repeat (3 {}", 'if "{" 1 {}']
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaisesRegex(SyntaxError, "line: .*column:"):
                    self._parse(source)

    def test_unclosed_control_bodies(self):
        """Reports missing closing braces for each kind of control body."""
        for source in ["if x {", "if x {} else {", "while x {", "repeat 3 {",
                       "forever {", "while x { if y {}"]:
            with self.subTest(source=source):
                with self.assertRaisesRegex(SyntaxError, "Missing closing token"):
                    self._parse(source)

    def test_control_flow_cannot_cross_sources(self):
        """Rejects bodies or else branches continued in a different source input."""
        for first, second in [("if x", "{}"), ("repeat 2 {", "}"),
                              ("if x {}", "else {}")]:
            with self.subTest(first=first, second=second):
                parser = Parser()
                parser.feed_text(first)
                parser.feed_text(second)
                with self.assertRaises(SyntaxError):
                    parser.build_ast()

    def test_nested_sprite_in_control_body_is_rejected(self):
        """Prevents a control body from being mistaken for global scope."""
        with self.assertRaisesRegex(SyntaxError, "global scope"):
            self._parse("if x { sprite Duck {} }")


if __name__ == '__main__':
    unittest.main()
