from uuid import uuid4
from enum import IntEnum
from typing import Union

from .exceptions import ScratchCompilerException


class InputType(IntEnum):
    LITERAL = 1
    BLOCK_INPUT = 2
    SHADOW_OVERRIDDEN = 3


class LiteralType(IntEnum):
    BLOCK_INPUT = 0
    STRING_LITERAL = 1  # e.g., "hello"
    BROADCAST_NAME = 2  # e.g., "message1"
    VARIABLE_NAME = 3  # Used in fields/definitions
    NUMBER_LITERAL = 4  # e.g., "10"
    COLOR_HEX_CODE = 5  # e.g., "#ff0000"
    LIST_NAME = 6  # Refers to lists
    SOUND_NAME = 7  # e.g., "Meow"
    COSTUME_NAME = 8  # e.g., "costume1"
    BACKDROP_NAME = 9  # e.g., "backdrop1"
    VARIABLE_SETTER_BLOCK = 10  # Opcode like "data_setvariableto"
    VARIABLE_GETTER_BLOCK = 11  # Opcode like "data_variable"
    VARIABLE_REFERENCE = 12  # e.g., [12, "myVar", "myVar"] in input
    LIST_REFERENCE = 13  # e.g., [13, "myList", "myList"]
    PROCEDURE_PARAMETER = 14  # Inputs in define blocks
    PROCEDURE_CALL = 15  # Calling custom blocks
    BROADCAST_REFERENCE = 16  # Refers to broadcasts in inputs
    COSTUME_NUMBER = 17  # Costume index value
    SCENE_NUMBER = 18  # Backdrop index value


class BlockType(IntEnum):
    REPORTER = 1  # (rounded) ones that report a value like add, subtract, sqrt, timer
    BOOLEAN = 2  # (hexagonal) like reporter but returns boolean
    ACTION = 3  # (rectangular) performs any action with given parameters
    HAT = 4  # (rounded top) like when flag clicked
    CAP = 5  # (flat bottom) ends script


class BlockDefinition:
    def __init__(self, opcode: str, block_type: BlockType, inputs: [str] = None, fields: [str] = None):
        if inputs is None:
            inputs = []
        if fields is None:
            fields = []
        if block_type is None:
            raise ScratchCompilerException(f"Block type cannot be None! opcode: {opcode}")

        self.opcode = opcode
        self.inputs = inputs
        self.fields = fields
        self.block_type = block_type


class Definitions:
    WHEN_FLAG_CLICKED = BlockDefinition("event_whenflagclicked", block_type=BlockType.HAT)
    MOVE_STEPS = BlockDefinition("motion_movesteps", inputs=["STEPS"], block_type=BlockType.ACTION)
    GOTO_XY = BlockDefinition("motion_gotoxy", inputs=["X", "Y"], block_type=BlockType.ACTION)

    SET_VARIABLE_TO = BlockDefinition("data_setvariableto", inputs=["VALUE"], fields=["VARIABLE"],
                                      block_type=BlockType.ACTION)

    LOOKS_SET_SIZE_TO = BlockDefinition("looks_setsizeto", inputs=["SIZE"], block_type=BlockType.ACTION)

    MATH_ADD = BlockDefinition("operator_add", inputs=["NUM1", "NUM2"], block_type=BlockType.REPORTER)

    OPERATOR_GT = BlockDefinition("operator_gt", inputs=["OPERAND1", "OPERAND2"], block_type=BlockType.BOOLEAN)

    CONTROL_IF = BlockDefinition("control_if", inputs=["CONDITION", "SUBSTACK"], block_type=BlockType.ACTION)


class Reference:
    def generate_reference(self) -> list:
        return []


class VariableReference(Reference):
    def __init__(self, variable_name: str, is_field_selector: bool = False):
        self.variable_name = variable_name
        self.is_field_selector = is_field_selector

    def generate_reference(self) -> list:
        if self.is_field_selector:
            return [self.variable_name, self.variable_name]
        return [
            InputType.SHADOW_OVERRIDDEN,
            [LiteralType.VARIABLE_REFERENCE, self.variable_name, self.variable_name],
            [LiteralType.NUMBER_LITERAL, 0]
        ]


class BlockReference(Reference):
    def __init__(self, block: "Block"):
        self.is_substack_reference = False
        if isinstance(block, Block):
            self.block_id = block.uuid
            return

        raise ScratchCompilerException(
            f"Only instance of {type(Block)} or {type(BlockStack)} can be passed in BlockReference. Got: {type(block)}")

    def generate_reference(self) -> list:
        return [InputType.BLOCK_INPUT, self.block_id]


class SubstackReference(Reference):
    def __init__(self, substack: "BlockStack", head_block: "Block"):
        self.substack = substack
        self.head_block = head_block

        if isinstance(substack, BlockStack):
            first_block: Union["Block", None] = substack.ordered_blocks[0] if len(substack.ordered_blocks) > 0 else None

            if first_block is None:
                raise ScratchCompilerException("Can't create empty substack reference!")

            first_block.set_parent(head_block, auto_set_child=False)
            self.substack = substack
            self.first_block_id = first_block.uuid
            return

        raise ScratchCompilerException("Provided substack isn't a BlockStack!")

    def generate_reference(self) -> list:
        return [InputType.BLOCK_INPUT, self.first_block_id]

    def get_substack(self) -> Union["BlockStack", None]:
        return self.substack


class Input:
    def __init__(self, value: Union[str, Reference, "Block"]):
        self.value = value
        self.use_reference = False
        self.use_block = False
        self.input_type = None
        self.literal_type = None

        if isinstance(value, str):
            self.input_type = InputType.LITERAL
            self.literal_type = LiteralType.STRING_LITERAL

            if value.isdigit() or value.isdecimal():
                self.literal_type = LiteralType.NUMBER_LITERAL
            return

        if isinstance(value, Reference):
            self.use_reference = True
            return

        if isinstance(value, Block):
            self.use_block = True

            block_definition = value.block_definition

            if block_definition.block_type not in [BlockType.REPORTER, BlockType.BOOLEAN, BlockType.ACTION,
                                                   BlockType.CAP]:
                raise ScratchCompilerException(
                    f"Block with type: {block_definition.block_type} cannot be used as an input!")
            return

        raise ScratchCompilerException(
            f"Invalid value given inside input: '{value}' typeof: {type(value)} expected 'str', 'Reference' or 'Block'!")

    def generate_input(self) -> list:
        if self.use_reference:
            return self.value.generate_reference()

        if self.use_block:
            return [InputType.SHADOW_OVERRIDDEN, self.value.uuid, [LiteralType.NUMBER_LITERAL, "0"]]

        if self.literal_type == LiteralType.BLOCK_INPUT:
            return [self.input_type, self.value]

        if self.input_type == InputType.LITERAL:
            return [self.input_type, [self.literal_type, self.value]]

        return [InputType.SHADOW_OVERRIDDEN, [self.input_type, [self.literal_type, self.value]],
                [LiteralType.NUMBER_LITERAL, 0]]


class FieldInput(Input):
    def __init__(self, value: Union[str, Reference]):
        super().__init__(value)

        if self.literal_type == LiteralType.NUMBER_LITERAL:
            raise ScratchCompilerException("Field value cannot be set to a number literal!")

    def generate_input(self) -> list:
        if isinstance(self.value, VariableReference):
            return self.value.generate_reference()

        raise ScratchCompilerException(
            f"Field input not implemented, input type: {self.input_type} literal type: {self.literal_type}, uses reference: {self.use_reference} value: {self.value}")


class Block:
    def __init__(self, block_definition: BlockDefinition):
        self.block_definition = block_definition
        self.parent = None
        self.child = None
        self.uuid = str(uuid4())
        self.input_values = {block_input: None for block_input in block_definition.inputs}
        self.field_values = {field_input: None for field_input in block_definition.fields}

    def generate_data(self) -> dict:
        for input_key, input_value in self.input_values.items():
            if input_value is None:
                raise ScratchCompilerException(
                    f"Input values not set for a block with opcode '{self.block_definition.opcode}' missing '{input_key}'")

        for field_key, field_value in self.field_values.items():
            if field_value is None:
                raise ScratchCompilerException(
                    f"Field values not set for a block with opcode '{self.block_definition.opcode}' missing '{field_key}'")

        block_data = {
            "opcode": self.block_definition.opcode,
            "next": self.child,
            "parent": self.parent,
            "inputs": self.input_values,
            "fields": self.field_values,
            "shadow": False,
            "topLevel": False,
        }

        if self.parent is None:
            block_data["topLevel"] = True
            block_data["x"] = 0
            block_data["y"] = 0

        return block_data

    def set_input_value(self, input_name: str, input_value: Input):
        if self.input_values[input_name] is not None:
            raise ScratchCompilerException(
                f"Input value of non existent input cannot be set! Input name: {input_name}, possible inputs: {self.block_definition.inputs}")

        input_is_block = isinstance(input_value.value, Block)

        if input_is_block and input_value.value.parent is not None:
            raise ScratchCompilerException("One reporter block cannot be set for input in different blocks!")

        if input_is_block:
            input_value.value.set_parent(self, auto_set_child=False)

        self.input_values[input_name] = input_value.generate_input()

    def set_field_value(self, field_name: str, field_value: FieldInput):
        if self.field_values[field_name] is not None:
            raise ScratchCompilerException(
                f"Field value of non existent field cannot be set! Field name: {field_name}, possible fields: {self.block_definition.fields}")

        self.field_values[field_name] = field_value.generate_input()

    def set_parent(self, parent_block: "Block", auto_set_child: bool = True):
        self.parent = parent_block.uuid
        if auto_set_child:
            parent_block.child = self.uuid

    def __str__(self):
        return f"Block({self.generate_data()})"


class BlockStack:
    def __init__(self):
        self.ordered_blocks = []
        self.unordered_blocks = []

    def add_block(self, new_block: Block, auto_parent: bool = True):
        if not auto_parent:
            if new_block in self.unordered_blocks:
                raise ScratchCompilerException(f"Can't add the same block again! Block data: {new_block}")
            self.unordered_blocks.append(new_block)
            return

        if new_block in self.ordered_blocks:
            raise ScratchCompilerException(f"Can't add the same block again! Block data: {new_block}")

        last_block = self.ordered_blocks[-1] if len(self.ordered_blocks) > 0 else None

        if last_block is not None:
            if new_block.parent is not None:
                raise ScratchCompilerException(f"Can't change the parent of a block that already has a parent!")
            new_block.set_parent(last_block)

        self.ordered_blocks.append(new_block)

    def generate_data(self) -> dict:
        blocks_dict = {}

        for block in self.ordered_blocks:
            blocks_dict[block.uuid] = block.generate_data()

        for block in self.unordered_blocks:
            blocks_dict[block.uuid] = block.generate_data()

        return blocks_dict
