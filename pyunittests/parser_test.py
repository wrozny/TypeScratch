import unittest

from Lang.parser import Parser
from Lang.scratch_ast import (
    EntryPoint, FunctionCall, MathOperation, ScratchOperator, SpriteDefinition,
    UnaryOperation, Value, VariableDeclaration, VariableReference, VariableSet,
)
from Lang.tokenizer import tokenize


class ParserTestCases(unittest.TestCase):
    """Verifies expression trees, statement dispatch and nested parser boundaries."""

    def _parse(self, text):
        """Builds the complete AST for the supplied test source."""
        parser = Parser()
        parser.feed_text(text)
        return parser.build_ast()

    def _expression(self, text):
        """Extracts the assigned expression from a test assignment."""
        return self._parse(f"a = {text}")[0].new_value

    def test_sprite_declaration(self):
        """Preserves multiple entry points and the call inside the second body."""
        nodes = self._parse('sprite Duck { @start {} @start { say("Mango") } }')
        self.assertEqual(len(nodes), 1)
        sprite = nodes[0]
        self.assertIsInstance(sprite, SpriteDefinition)
        self.assertEqual(sprite.name, "Duck")
        self.assertEqual(len(sprite.entry_points), 2)
        self.assertEqual(sprite.entry_points[0].body, [])
        call = sprite.entry_points[1].body[0]
        self.assertIsInstance(call, FunctionCall)
        self.assertEqual(call.function_name, "say")
        self.assertEqual(call.arguments[0].value, "Mango")

    def test_empty_sprite_entry_point(self):
        """Preserves the local test case with a single empty entry point."""
        sprite = self._parse("sprite Duck { @start {} }")[0]
        self.assertEqual(sprite.name, "Duck")
        self.assertEqual(len(sprite.entry_points), 1)
        self.assertEqual(sprite.entry_points[0].body, [])

    def test_decorators(self):
        """Parses adjacent entry points without skipping the second decorator."""
        nodes = self._parse("@start {} @start {}")
        self.assertEqual(len(nodes), 2)
        self.assertTrue(all(isinstance(node, EntryPoint) for node in nodes))

    def test_multiple_sprites(self):
        """Restores global context after each sprite definition."""
        nodes = self._parse("sprite Duck {} sprite Cat {}")
        self.assertEqual([node.name for node in nodes], ["Duck", "Cat"])

    def test_declaration_with_initializer(self):
        """Returns a declaration followed by its initializer assignment."""
        declaration, assignment = self._parse("let a = 10")
        self.assertIsInstance(declaration, VariableDeclaration)
        self.assertTrue(declaration.is_global)
        self.assertEqual(declaration.variable_name, "a")
        self.assertIsInstance(assignment, VariableSet)
        self.assertEqual(assignment.variable_name, "a")
        self.assertEqual(assignment.new_value.value, "10")
        self.assertEqual(assignment.instruction_name, "__setvariableto")

    def test_declaration_without_initializer(self):
        """Allows an uninitialized declaration followed by an assignment."""
        nodes = self._parse("let a\na = 20")
        self.assertEqual(len(nodes), 2)
        self.assertIsInstance(nodes[0], VariableDeclaration)
        self.assertIsInstance(nodes[1], VariableSet)

    def test_entry_point_preserves_declarations(self):
        """Retains declarations, assignments and calls in their original order."""
        body = self._parse('@start { let x = 10\nsay(x)\nx = 20 }')[0].body
        self.assertEqual([type(node) for node in body],
                         [VariableDeclaration, VariableSet, FunctionCall, VariableSet])
        self.assertFalse(body[0].is_global)
        self.assertEqual(body[2].arguments[0].variable_name, "x")

    def test_sprite_initializer_is_retained(self):
        """Keeps sprite initializer instructions in the complete ordered body."""
        sprite = self._parse("sprite Duck { let x = 10\n@start {} }")[0]
        self.assertEqual([type(node) for node in sprite.body],
                         [VariableDeclaration, VariableSet, EntryPoint])
        self.assertFalse(sprite.variable_declarations[0].is_global)

    def test_values_share_one_class(self):
        """Uses Value for numeric and string literals without separate literal classes."""
        for text, value in [('12.5', '12.5'), ('"hello"', 'hello'), ("'12.5'", '12.5')]:
            with self.subTest(text=text):
                expression = self._expression(text)
                self.assertIsInstance(expression, Value)
                self.assertEqual(expression.value, value)

    def test_identifier_reference(self):
        """Parses an identifier without assignment as a variable reference."""
        reference = self._parse("some_variable")[0]
        self.assertIsInstance(reference, VariableReference)
        self.assertEqual(reference.variable_name, "some_variable")

    def test_identifier_expression(self):
        """Preserves binary expressions starting with an identifier."""
        expression = self._parse("x + 2")[0]
        self.assertEqual(expression.operator, ScratchOperator.ADD)
        self.assertEqual(expression.left_value.variable_name, "x")

    def test_arithmetic_precedence(self):
        """Groups multiplication inside addition."""
        expression = self._expression("10 + 3 * 2")
        self.assertEqual(expression.operator, ScratchOperator.ADD)
        self.assertEqual(expression.left_value.value, "10")
        self.assertEqual(expression.right_value.operator, ScratchOperator.MULTIPLY)
        self.assertEqual(expression.right_value.left_value.value, "3")
        self.assertEqual(expression.right_value.right_value.value, "2")

    def test_parentheses_override_precedence(self):
        """Groups an explicitly parenthesized sum before multiplication."""
        expression = self._expression("(10 + 3) * 2")
        self.assertEqual(expression.operator, ScratchOperator.MULTIPLY)
        self.assertEqual(expression.left_value.operator, ScratchOperator.ADD)

    def test_left_associativity(self):
        """Groups subtraction and division from left to right."""
        for source, operator in [("10 - 3 - 2", ScratchOperator.SUBTRACT),
                                 ("12 / 3 / 2", ScratchOperator.DIVIDE)]:
            with self.subTest(source=source):
                expression = self._expression(source)
                self.assertEqual(expression.operator, operator)
                self.assertEqual(expression.left_value.operator, operator)
                self.assertEqual(expression.right_value.value, "2")

    def test_logical_and_comparison_precedence(self):
        """Groups arithmetic, relational, equality, and logical operations in order."""
        expression = self._expression("x + 1 > 2 == y and z or q")
        self.assertEqual(expression.operator, ScratchOperator.OR)
        conjunction = expression.left_value
        self.assertEqual(conjunction.operator, ScratchOperator.AND)
        equality = conjunction.left_value
        self.assertEqual(equality.operator, ScratchOperator.EQUAL)
        comparison = equality.left_value
        self.assertEqual(comparison.operator, ScratchOperator.GREATER_THAN)
        self.assertEqual(comparison.left_value.operator, ScratchOperator.ADD)

    def test_original_expression(self):
        """Builds the expected tree for division, conjunction and multiplied calls."""
        expression = self._expression("(10 / 3) and check_some(30) * sin(30)")
        self.assertEqual(expression.operator, ScratchOperator.AND)
        self.assertEqual(expression.left_value.operator, ScratchOperator.DIVIDE)
        product = expression.right_value
        self.assertEqual(product.operator, ScratchOperator.MULTIPLY)
        self.assertEqual(product.left_value.function_name, "check_some")
        self.assertEqual(product.right_value.function_name, "sin")

    def test_nested_calls(self):
        """Keeps nested calls and arithmetic argument trees in evaluation order."""
        call = self._expression("add(add(1, 2), add(3, 4 * 5))")
        self.assertEqual(call.function_name, "add")
        self.assertEqual(len(call.arguments), 2)
        self.assertEqual([argument.function_name for argument in call.arguments], ["add", "add"])
        self.assertEqual([value.value for value in call.arguments[0].arguments], ["1", "2"])
        self.assertEqual(call.arguments[1].arguments[1].operator, ScratchOperator.MULTIPLY)

    def test_call_without_arguments(self):
        """Accepts a named call with an empty argument list."""
        call = self._parse("check_some()")[0]
        self.assertIsInstance(call, FunctionCall)
        self.assertEqual(call.arguments, [])

    def test_unary_operators(self):
        """Binds unary operators more tightly than multiplication and conjunction."""
        expression = self._expression("-x * 2 and !not y")
        self.assertEqual(expression.operator, ScratchOperator.AND)
        negative = expression.left_value.left_value
        self.assertIsInstance(negative, UnaryOperation)
        self.assertEqual(negative.operator, "-")
        self.assertEqual(negative.operand.variable_name, "x")
        negation = expression.right_value
        self.assertEqual(negation.operator, "!")
        self.assertEqual(negation.operand.operator, "not")

    def test_compound_assignments(self):
        """Expands compound assignments into a variable set with a binary value."""
        operators = {"+=": ScratchOperator.ADD, "-=": ScratchOperator.SUBTRACT,
                     "*=": ScratchOperator.MULTIPLY, "/=": ScratchOperator.DIVIDE,
                     "%=": ScratchOperator.MODULO}
        for spelling, operator in operators.items():
            with self.subTest(operator=spelling):
                assignment = self._parse(f"x {spelling} 2 + 3")[0]
                self.assertIsInstance(assignment, VariableSet)
                self.assertEqual(assignment.new_value.operator, operator)
                self.assertEqual(assignment.new_value.left_value.variable_name, "x")
                self.assertEqual(assignment.new_value.right_value.operator, ScratchOperator.ADD)

    def test_multiline_arguments_and_groups(self):
        """Accepts line breaks inside grouping and nested call arguments."""
        expression = self._expression("add(\n (1 +\n 2),\n sin(\n30\n)\n)")
        self.assertEqual(len(expression.arguments), 2)
        self.assertEqual(expression.arguments[0].operator, ScratchOperator.ADD)
        self.assertEqual(expression.arguments[1].function_name, "sin")

    def test_newlines_and_semicolons(self):
        """Stops expressions at statement boundaries without swallowing the next statement."""
        nodes = self._parse("let a = 1; a += 2\nsay(a)\nlet b")
        self.assertEqual([type(node) for node in nodes],
                         [VariableDeclaration, VariableSet, VariableSet, FunctionCall, VariableDeclaration])

    def test_operator_spellings(self):
        """Parses each supported comparison and modulo operator."""
        operators = {"==": ScratchOperator.EQUAL, "!=": ScratchOperator.NOT_EQUAL,
                     "<": ScratchOperator.LESS_THAN, ">": ScratchOperator.GREATER_THAN,
                     "<=": ScratchOperator.LESS_EQUAL, ">=": ScratchOperator.GREATER_EQUAL,
                     "%": ScratchOperator.MODULO}
        for spelling, operator in operators.items():
            with self.subTest(operator=spelling):
                self.assertEqual(self._expression(f"x {spelling} 2").operator, operator)

    def test_string_content_is_not_syntax(self):
        """Keeps quote characters, delimiters and operator text inside string values."""
        sources = [('"\'quoted\'"', "'quoted'"), ("'\"quoted\"'", '"quoted"'),
                   ('"and"', "and"), ('"*"', "*"), ('"a,b);}"', "a,b);}")]
        for source, expected in sources:
            with self.subTest(source=source):
                self.assertEqual(self._expression(source).value, expected)

    def test_positions(self):
        """Preserves source coordinates on references, calls and binary operators."""
        expression = self._parse("\na = x + sin(30)")[0].new_value
        self.assertEqual((expression.line, expression.column), (2, 6))
        self.assertEqual((expression.left_value.line, expression.left_value.column), (2, 4))
        self.assertEqual((expression.right_value.line, expression.right_value.column), (2, 8))

    def test_parser_preserves_tokens(self):
        """Leaves both external and parser token lists intact after nested parsing."""
        tokens = tokenize('sprite Duck { @start { let x = (1 + 2)\nsay(x) } }')
        original = tokens.copy()
        parser = Parser()
        parser.feed_tokens(tokens)
        parser.build_ast()
        self.assertEqual(tokens, original)
        self.assertEqual(parser.tokens, original)
        self.assertIsNot(parser.tokens, tokens)
        self.assertEqual(parser.current_token_index, len(original))

    def test_multiple_source_feeds(self):
        """Parses all appended sources without merging expressions across file boundaries."""
        parser = Parser()
        parser.feed_text("let x = 1")
        parser.feed_text("x = 2")
        nodes = parser.build_ast()
        self.assertEqual(len(nodes), 3)
        self.assertEqual(nodes[-1].new_value.value, "2")

    def test_empty_input(self):
        """Returns no nodes for empty input or separator-only input."""
        self.assertEqual(self._parse(""), [])
        self.assertEqual(self._parse("\n;\n"), [])

    def test_invalid_expressions(self):
        """Rejects incomplete, ambiguous or unsupported expressions with positioned errors."""
        sources = ["a =", "a = 1 +", "a = ()", "a = (1 + 2", "a = 1)",
                   "a = add(1 2)", "a = add(,1)", "a = add(1,)", "a = add(1,,2)",
                   "a = add(x = 1)", "a = 1 2", "a = x = 2", "let = 1",
                   "let x += 1", "let x 10", 'let x "=" 10', "a = * 2", "a = add(1;2)",
                   "a = 1 +\n2", "a = f()(1)", "a = (1\n}"]
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaisesRegex(SyntaxError, "line: .*column:"):
                    self._parse(source)

    def test_unclosed_blocks(self):
        """Rejects unterminated blocks including token lists without an EOF marker."""
        for source in ["sprite Duck {", "@start { a = 1", "sprite Duck { @start {}"]:
            with self.subTest(source=source):
                with self.assertRaisesRegex(SyntaxError, "Missing closing token"):
                    self._parse(source)
        parser = Parser()
        parser.feed_tokens(tokenize("@start {")[:-1])
        with self.assertRaisesRegex(SyntaxError, "Missing closing token"):
            parser.build_ast()

    def test_nested_sprite_is_rejected(self):
        """Rejects sprite declarations outside the global parser context."""
        with self.assertRaisesRegex(SyntaxError, "global scope"):
            self._parse("sprite Duck { sprite Cat {} }")


if __name__ == '__main__':
    unittest.main()
