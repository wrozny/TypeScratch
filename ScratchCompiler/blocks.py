from uuid import uuid4
from enum import IntEnum, StrEnum
from typing import Union

from .exceptions import ScratchCompilerException


class InputType(IntEnum):
    """
        Enum class that defines different input types for scratch like:
        if input is just a value, reference to some block or a reference with a value under it, respectively
    """
    LITERAL = 1
    BLOCK_INPUT = 2
    SHADOW_OVERRIDDEN = 3


class LiteralType(IntEnum):
    """
        Enum class that tells the exact value type inside an input like:
        if input is a number, string, variable reference, variable name etc.

        Those enums were generated with AI, it's not wise to believe these values are real
        though these only get used internally, both InputType and LiteralType enums
        are used in implementations of Reference class descendants only and Input class itself.

        VERY IMPORTANT!!!!
        If someone is looking back at this (includes me) and need to use this
        please make sure these actually match the numbers used in scratch!
    """
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


class BlockType(StrEnum):
    """
        Enum class for every type of block inside scratch.
    """
    REPORTER = "Reporter"  # (rounded) ones that report a value like add, subtract, sqrt, timer
    BOOLEAN = "Boolean"  # (hexagonal) like reporter but returns boolean
    COMMAND = "Command"  # (rectangular) performs any command with given parameters like move steps
    HAT = "Hat"  # (rounded top) like when flag clicked
    CAP = "Cap"  # (flat bottom) ends script


class BlockDefinition:
    """
        Class used for defining a scratch block template
        bunch of definitions are hardcoded in Definitions class but with
        this class you can create block definitions at runtime for blocks from
        different scratch extensions that aren't defined by default.
    """

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
    """
        Class with hardcoded scratch block definitions
    """

    WHEN_FLAG_CLICKED = BlockDefinition("event_whenflagclicked", block_type=BlockType.HAT)
    MOVE_STEPS = BlockDefinition("motion_movesteps", inputs=["STEPS"], block_type=BlockType.COMMAND)
    GOTO_XY = BlockDefinition("motion_gotoxy", inputs=["X", "Y"], block_type=BlockType.COMMAND)

    SET_VARIABLE_TO = BlockDefinition("data_setvariableto", inputs=["VALUE"], fields=["VARIABLE"],
                                      block_type=BlockType.COMMAND)

    LOOKS_SET_SIZE_TO = BlockDefinition("looks_setsizeto", inputs=["SIZE"], block_type=BlockType.COMMAND)

    MATH_ADD = BlockDefinition("operator_add", inputs=["NUM1", "NUM2"], block_type=BlockType.REPORTER)

    OPERATOR_GT = BlockDefinition("operator_gt", inputs=["OPERAND1", "OPERAND2"], block_type=BlockType.BOOLEAN)

    CONTROL_IF = BlockDefinition("control_if", inputs=["CONDITION", "SUBSTACK"], block_type=BlockType.COMMAND)


class Reference:
    """
        Base class for any type of LiteralType reference
    """

    def generate_reference(self) -> list:
        """
        Generates reference to a corresponding scratch LiteralType
        :return: list defining a reference
        """
        return []


class VariableReference(Reference):
    """
        Used for creating a reference to a variable for both normal Input and FieldInput
    """

    def __init__(self, variable_name: str, is_field_selector: bool = False):
        """
        :param variable_name: Name of variable to refer to
        :param is_field_selector: Defines if reference used in a field
        """
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


class SubstackReference(Reference):
    """
        Used for creating a reference to a substack of blocks; Used for blocks that branch off to different blocks.
    """

    def __init__(self, substack: "BlockStack", head_block: "Block"):
        """
        :param substack: The stack of blocks
        :param head_block: Block that blocks are getting branched from
        """
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


class Input:
    """
        Wrapper for any type of input needed for any given block
    """

    def __init__(self, value: Union[str, Reference, "Block"]):
        """
        :param value: String with value, reference object or a block object
        WARNING! Numbers should be also passed in as a string!
        """
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

            if block_definition.block_type not in [BlockType.REPORTER, BlockType.BOOLEAN, BlockType.COMMAND,
                                                   BlockType.CAP]:
                raise ScratchCompilerException(
                    f"Block with type: {block_definition.block_type} cannot be used as an input!")
            return

        raise ScratchCompilerException(
            f"Invalid value given inside input: '{value}' typeof: {type(value)} expected 'str', 'Reference' or 'Block'!")

    def generate_input(self) -> list:
        """
        Generates the scratch input list
        :return: Scratch input data list
        """
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
    """
        Wrapper for field inputs
    """

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
    """
        Used for creating a scratch block instance
    """

    def __init__(self, block_definition: BlockDefinition):
        self.block_definition = block_definition
        self.parent = None
        self.child = None
        self.uuid = str(uuid4())
        self.input_values = {block_input: None for block_input in block_definition.inputs}
        self.field_values = {field_input: None for field_input in block_definition.fields}

    def generate_data(self) -> dict:
        """
        Generates the data of a block to be included in final .sb3 project
        :return: Dictionary of block values
        """

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
        """
        Sets the input value of a block
        :param input_name: The name of input defined in the block definition
        :param input_value: Instance of Input class
        """
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
        """
        Sets the field value of a block
        :param field_name: The name of field defined in the block definition
        :param field_value: Instance of FieldInput class
        """
        if self.field_values[field_name] is not None:
            raise ScratchCompilerException(
                f"Field value of non existent field cannot be set! Field name: {field_name}, possible fields: {self.block_definition.fields}")

        self.field_values[field_name] = field_value.generate_input()

    def set_parent(self, parent_block: "Block", auto_set_child: bool = True):
        """
        Sets the parent of the block
        :param parent_block: The parent block
        :param auto_set_child: Defines if parents child can be set to this block
        """
        self.parent = parent_block.uuid
        if auto_set_child:
            parent_block.child = self.uuid

    def __str__(self):
        return f"Block({self.generate_data()})"


class BlockStack:
    """
        Stack data structure that stores blocks and automatically sets their parent and child
        unless explicitly disabled for each block
    """

    def __init__(self):
        self.ordered_blocks = []
        self.unordered_blocks = []

    def add_block(self, new_block: Block, auto_parent: bool = True):
        """
        Adds new block to the stack
        :param new_block: New block to be added
        :param auto_parent: Defines if parent of new block should be automatically set
        """
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
        """
        Generates the data to be used in final .sb3 project file from all added blocks
        :return: Dictionary of block id to block data
        """
        blocks_dict = {}

        for block in self.ordered_blocks:
            blocks_dict[block.uuid] = block.generate_data()

        for block in self.unordered_blocks:
            blocks_dict[block.uuid] = block.generate_data()

        return blocks_dict
