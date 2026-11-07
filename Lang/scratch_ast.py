from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


@dataclass
class ASTNode:
    """
    Defines abstract syntax tree node. Direct result of parsing.
    All nodes by default store the line and column where they started to be parsed
    """
    line: int
    column: int


@dataclass
class Reporter(ASTNode):
    """
    Defines every reporter block (the rounded block in scratch that returns a value)
    """
    pass


@dataclass
class Instruction(ASTNode):
    """
    Defines instruction blocks, where:

    instruction name is used as an identifier for instructions lookup dictionary
    which later defines how positional arguments translate
    into actual project.json complex structures of that certain instruction
    """
    instruction_name: str
    arguments: list[Reporter]


@dataclass
class Value(Reporter):
    """
    Defines a literal value, this includes numbers and strings.
    Scratch doesn't differentiate numbers and strings until the usage context is known,

    e.g a math addition operation of 2 strings results in arithmetic sum if possible,
    Parsed literal values retain their text, leaving numeric conversion to Scratch.
    Manually constructed values may also contain a Python integer or float.
    """
    value: str | int | float


LiteralValue = Value


@dataclass
class VariableDeclaration(ASTNode):
    """
    Defines a variable with given variable name,
    variables are non-global by default unless defined outside sprite space or with a "global" modifier
    """
    variable_name: str
    is_global: bool = False


@dataclass
class VariableSet(Instruction):
    """
    Defines the "Set Variable" block in scratch or in parse terms the operation of setting a variable
    """
    variable_name: str
    new_value: Reporter
    instruction_name: str = field(default="__setvariableto", init=False)


@dataclass
class VariableReference(Reporter):
    """
    Defines a variable reference to variable with specific variable name
    variable_identifier is used to differentiate same variable names in different scopes,
    it's later set by the NameResolver from ast_resolution.py
    """
    variable_name: str
    variable_identifier: str | None = None


@dataclass
class EntryPoint(Instruction):
    """
    Defines abstraction for scratch event blocks like
    when flag clicked or when key pressed (key)
    """
    body: list[ASTNode]


@dataclass
class ProcedureDefinition(EntryPoint):
    procedure_name: str
    parameters: list[str]


@dataclass
class ParameterReference(Reporter):
    """
    Defines a reference to a procedure parameter
    """
    parameter_name: str


class ScratchOperator(StrEnum):
    """
    Enum representing reporters from scratch operators tab
    """

    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_EQUAL = "GREATER_EQUAL"
    AND = "AND"
    OR = "OR"


@dataclass
class MathOperation(Reporter):
    """Defines a binary arithmetic, comparison or logical expression."""
    operator: ScratchOperator
    left_value: Reporter
    right_value: Reporter


@dataclass
class UnaryOperation(Reporter):
    """Defines a unary expression before translation into Scratch reporters."""
    operator: str
    operand: Reporter


@dataclass
class FunctionCall(Reporter):
    """Defines a named call without deciding whether it is a native reporter or procedure."""
    function_name: str
    arguments: list[Reporter]


@dataclass
class Conditional(ASTNode):
    """Defines a condition and its branches; None means no else branch was written."""
    condition: Reporter
    body: list[ASTNode]
    else_body: list[ASTNode] | None = None


@dataclass
class WhileLoop(ASTNode):
    """Defines a loop whose condition is checked before every iteration."""
    condition: Reporter
    body: list[ASTNode]


@dataclass
class RepeatLoop(ASTNode):
    """Defines a loop whose iteration count is evaluated once on entry."""
    count: Reporter
    body: list[ASTNode]


@dataclass
class ForeverLoop(ASTNode):
    """Defines an unconditional loop with no expression in its header."""
    body: list[ASTNode]


@dataclass
class SpriteDefinition(ASTNode):
    """Defines a sprite with all its declarations and entry points in source order."""
    name: str
    body: list[ASTNode] = field(default_factory=list)


@dataclass
class VirtualSpriteDefinition(SpriteDefinition):
    pass
