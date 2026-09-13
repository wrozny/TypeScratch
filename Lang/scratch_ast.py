from __future__ import annotations
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
class Reporter(ASTNode):
    """
    Defines every reporter block (the rounded block in scratch that returns a value)
    """
    pass


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
class VariableDeclaration(ASTNode):
    """
    Defines a variable with given variable name,
    variables are non-global by default unless defined outside sprite space or with a "global" modifier
    """
    variable_name: str
    is_global: bool = False


@dataclass
class VariableSet(ASTNode):
    """
    Defines the "Set Variable" block in scratch or in parse terms the operation of setting a variable
    """
    variable_name: str
    new_value: Reporter


@dataclass
class EntryPoint(ASTNode):
    body: list[ASTNode]


@dataclass
class VariableReference(Reporter):
    """
    Defines a variable reference to variable with specific variable name
    """
    variable_name: str


@dataclass
class ParameterReference(Reporter):
    """
    Defines a reference to a procedure parameter
    """
    parameter_name: str


@dataclass
class ProcedureDefinition(EntryPoint):
    procedure_name: str
    parameters: list[str]


@dataclass
class Instruction(ASTNode):
    pass


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
    procedures: list[ProcedureDefinition]
    variable_declarations: list[VariableDeclaration]


@dataclass
class VirtualSpriteDefinition(SpriteDefinition):
    pass
