from dataclasses import dataclass
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
class LiteralValue(ASTNode):
    """
    Defines a literal value, this includes numbers and strings.
    Scratch doesn't differentiate numbers and strings until the usage context is known,

    e.g a math addition operation of 2 strings results in arithmetic sum if possible,
    so all values are strings by default.
    """
    value: str


@dataclass
class Reporter(ASTNode):
    """
    Defines every reporter block (the rounded block in scratch that returns a value)
    """
    pass


@dataclass
class VariableDefinition(ASTNode):
    """
    Defines a variable definition that creates a variable with given variable name,
    variables are non-global by default unless defined outside sprite space or with a "global" modifier
    """
    variable_name: str
    is_global: bool = False


@dataclass
class VariableReference(Reporter):
    """
    Defines a variable reference to variable with specific variable name
    """
    variable_name: str


class ScratchOperator(StrEnum):
    """
    Enum representing reporters from scratch operators tab
    """

    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"


@dataclass
class MathOperation(Reporter):
    operator: ScratchOperator
    left_value: LiteralValue | Reporter
    right_value: LiteralValue | Reporter


@dataclass
class BlockDefinition:
    opcode: str


@dataclass
class EntryPoint(BlockDefinition):
    pass


@dataclass
class SpriteDefinition(ASTNode):
    name: str
    entry_points: list[EntryPoint]


@dataclass
class VirtualSpriteDefinition(SpriteDefinition):
    pass


@dataclass
class Program(ASTNode):
    block_definitions: dict[str, BlockDefinition]
    sprites: list[SpriteDefinition]
    stage: SpriteDefinition | None
