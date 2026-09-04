import json
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

    SAY = BlockDefinition("looks_say", inputs=["MESSAGE"], block_type=BlockType.COMMAND)

    TURN_RIGHT = BlockDefinition("motion_turnright", inputs=["DEGREES"], block_type=BlockType.COMMAND)
    TURN_LEFT = BlockDefinition("motion_turnleft", inputs=["DEGREES"], block_type=BlockType.COMMAND)

    GOTO_XY = BlockDefinition("motion_gotoxy", inputs=["X", "Y"], block_type=BlockType.COMMAND)

    SET_VARIABLE_TO = BlockDefinition("data_setvariableto", inputs=["VALUE"], fields=["VARIABLE"],
                                      block_type=BlockType.COMMAND)
    CHANGE_VARIABLE_BY = BlockDefinition("data_changevariableby", inputs=["VALUE"], fields=["VARIABLE"],
                                         block_type=BlockType.COMMAND)

    LOOKS_SET_SIZE_TO = BlockDefinition("looks_setsizeto", inputs=["SIZE"], block_type=BlockType.COMMAND)

    MATH_ADD = BlockDefinition("operator_add", inputs=["NUM1", "NUM2"], block_type=BlockType.REPORTER)

    OPERATOR_GT = BlockDefinition("operator_gt", inputs=["OPERAND1", "OPERAND2"], block_type=BlockType.BOOLEAN)

    CONTROL_IF = BlockDefinition("control_if", inputs=["CONDITION", "SUBSTACK"], block_type=BlockType.COMMAND)
    CONTROL_REPEAT = BlockDefinition("control_repeat", inputs=["TIMES", "SUBSTACK"], block_type=BlockType.COMMAND)
    CONTROL_REPEAT_UNTIL = BlockDefinition("control_repeat_until", inputs=["SUBSTACK", "CONDITION"],
                                           block_type=BlockType.COMMAND)
    CONTROL_FOREVER = BlockDefinition("control_forever", inputs=["SUBSTACK"], block_type=BlockType.CAP)


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

            first_block.connect_parent(head_block, auto_set_child=False)
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

    def __init__(self, value: Union[str, Reference, "Block"], force_input_type: InputType | None = None):
        """
        :param value: String with value, reference object or a block object
        WARNING! Numbers should be also passed in as a string!
        """
        self.value = value
        self.use_reference = False
        self.use_block = False
        self.input_type = None
        self.literal_type = None

        resolved_value_type = False

        if isinstance(value, str):
            self.input_type = InputType.LITERAL
            self.literal_type = LiteralType.STRING_LITERAL

            if value.isdigit() or value.isdecimal():
                self.literal_type = LiteralType.NUMBER_LITERAL
            resolved_value_type = True

        if isinstance(value, Reference):
            self.use_reference = True
            resolved_value_type = True

        if isinstance(value, Block):
            self.use_block = True

            block_definition = value.block_definition

            if block_definition.block_type not in [BlockType.REPORTER, BlockType.BOOLEAN, BlockType.COMMAND,
                                                   BlockType.CAP]:
                raise ScratchCompilerException(
                    f"Block with type: {block_definition.block_type} cannot be used as an input!")
            resolved_value_type = True

        if force_input_type is not None:
            self.input_type = force_input_type

        if resolved_value_type:
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

        if self.input_type == InputType.BLOCK_INPUT:
            if self.use_block:
                return [self.input_type, self.value.uuid]
            return [self.input_type, self.value]

        if self.input_type == InputType.LITERAL:
            return [self.input_type, [self.literal_type, self.value]]

        if self.use_block:
            return [InputType.SHADOW_OVERRIDDEN, self.value.uuid, [LiteralType.NUMBER_LITERAL, "0"]]

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


class ReporterField(Input):
    """
        Wrapper for fields inside reporter blocks
    """

    def __init__(self, value: Union[str, Reference]):
        super().__init__(value)

        if self.literal_type != LiteralType.STRING_LITERAL:
            raise ScratchCompilerException(f"Reporter input can only be a 'str'! Got {type(self.value)}")

    def generate_input(self) -> list:
        return [self.value, None]


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
        self.mutation = None

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

        if self.mutation is not None:
            block_data["mutation"] = self.mutation

        if self.parent is None:
            block_data["topLevel"] = True
            block_data["x"] = 0
            block_data["y"] = 0

        return block_data

    def set_input_value(self, input_name: str, input_value: Input, ignore_safety: bool = False):
        """
        Sets the input value of a block
        :param input_name: The name of input defined in the block definition
        :param input_value: Instance of Input class
        :param ignore_safety: Tells whether to ignore some safety checks like: *input in definition*
        """

        if input_name not in self.input_values and not ignore_safety:
            raise ScratchCompilerException(
                f"Input value of non existent input cannot be set! Input name: {input_name}, possible inputs: {self.block_definition.inputs}")

        input_is_block = isinstance(input_value.value, Block)

        if input_is_block and input_value.value.parent is not None:
            raise ScratchCompilerException("One reporter block cannot be set for input in different blocks!")

        if input_is_block:
            input_value.value.connect_parent(self, auto_set_child=False)

        self.input_values[input_name] = input_value.generate_input()

    def set_field_value(self, field_name: str, field_value: Union[FieldInput, ReporterField]):
        """
        Sets the field value of a block
        :param field_name: The name of field defined in the block definition
        :param field_value: Instance of FieldInput class
        """
        if self.field_values[field_name] is not None:
            raise ScratchCompilerException(
                f"Field value of non existent field cannot be set! Field name: {field_name}, possible fields: {self.block_definition.fields}")

        self.field_values[field_name] = field_value.generate_input()

    def connect_parent(self, parent_block: "Block", auto_set_child: bool = True):
        """
        Sets the parent of a child and child of the parent unless explicitly defined not to
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

    @property
    def first_block(self) -> Block | None:
        """
        :return: first block
        """
        return self.ordered_blocks[0]

    def empty(self) -> bool:
        """
        :return: boolean whether block stack is empty or not
        """
        return len(self.ordered_blocks) == 0

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
            new_block.connect_parent(last_block)

        self.ordered_blocks.append(new_block)

    def generate_data(self) -> dict:
        """
        Generates the data to be used in final .sb3 project file from all added blocks.
        :return: Dictionary of block id to block data
        """
        blocks_dict = {}

        for block in self.ordered_blocks:
            blocks_dict[block.uuid] = block.generate_data()

        for block in self.unordered_blocks:
            blocks_dict[block.uuid] = block.generate_data()

        return blocks_dict


class Procedure:
    """
        Class defining procedure logic, scratch saves a lot of unique information for this
    """

    def __init__(self, procedure_name: str, parameters: list[str] | None = None, use_warp: bool = False):
        self.procedure_name = procedure_name
        self.unordered_blocks = []
        self.ordered_blocks = []
        self.current_block_stack: BlockStack | None = None

        self.use_warp = use_warp

        self.parameters = parameters if parameters is not None else []

        self.parameter_blocks = []

        arg_reporter_definition = BlockDefinition("argument_reporter_string_number", fields=["VALUE"],
                                                  block_type=BlockType.REPORTER)

        for parameter_name in self.parameters:
            new_reporter = Block(arg_reporter_definition)
            new_reporter.set_field_value("VALUE", ReporterField(parameter_name))
            self.parameter_blocks.append(new_reporter)

        self.call_block_definition = BlockDefinition("procedures_call",
                                                     inputs=[reporter.uuid for reporter in self.parameter_blocks],
                                                     block_type=BlockType.COMMAND)
        self.call_block_mutation = {
            "tagName": "mutation",
            "children": [],
            "proccode": f"{self.procedure_name} {' '.join(['%s'] * len(self.parameter_blocks))}",
            "argumentids": json.dumps([reporter.uuid for reporter in self.parameter_blocks]),
            "warp": "true" if self.use_warp else "false"
        }

    def get_parameter_as_input(self, parameter_name: str) -> Input:
        """
        Creates Input object with reference to provided parameter block
        and automatically includes the block in final json
        :return: The input reference to a parameter
        """

        if parameter_name not in self.parameters:
            raise ScratchCompilerException(
                f"Tried to reference parameter '{parameter_name}' but procedure only supports ({self.parameters})")

        argument_reporter_definition = BlockDefinition("argument_reporter_string_number", fields=["VALUE"],
                                                       block_type=BlockType.REPORTER)
        argument_reporter_block = Block(argument_reporter_definition)
        argument_reporter_block.set_field_value("VALUE", ReporterField(parameter_name))

        self.unordered_blocks.append(argument_reporter_block)

        return Input(argument_reporter_block)

    def set_block_stack(self, block_stack: BlockStack):
        """
        Adds the set block stack to the procedure definition
        :param block_stack: Block stack
        """
        self.current_block_stack = block_stack

    def generate_call_block(self, arguments: list[Input]) -> Block:
        """
        Generates a block that calls this procedure with provided arguments
        :return: procedure call block
        """

        if len(arguments) != len(self.parameter_blocks):
            raise ScratchCompilerException(
                f"Procedure {self.procedure_name} requires {len(self.parameter_blocks)} arguments but {len(arguments)} were given!")

        call_block = Block(self.call_block_definition)

        for argument, reporter in list(zip(arguments, self.parameter_blocks)):
            call_block.set_input_value(reporter.uuid, argument)

        call_block.mutation = self.call_block_mutation

        return call_block

    def generate_procedure_data(self) -> dict:
        """
        Generates a dictionary with all blocks used in the procedure.
        :return: procedure data
        """

        procedure_definition_block = Block(
            BlockDefinition("procedures_definition", inputs=["custom_block"], block_type=BlockType.HAT))

        procedure_prototype_block = Block(BlockDefinition("procedures_prototype", block_type=BlockType.COMMAND))

        procedure_definition_block.set_input_value("custom_block", Input(procedure_prototype_block,
                                                                         force_input_type=InputType.BLOCK_INPUT))

        procedure_prototype_block.connect_parent(procedure_definition_block, auto_set_child=False)
        procedure_prototype_block.mutation = {
            "tagName": "mutation",
            "children": [],
            "proccode": f"{self.procedure_name} {' '.join(['%s'] * len(self.parameter_blocks))}",
            "argumentids": json.dumps([reporter.uuid for reporter in self.parameter_blocks]),
            "argumentnames": json.dumps(self.parameters),
            "argumentdefaults": json.dumps([""] * len(self.parameter_blocks) + ["false"] * len(self.parameter_blocks)),
            "warp": json.dumps(self.use_warp)
        }

        prototype_block_data = procedure_prototype_block.generate_data()
        prototype_block_data["shadow"] = True

        for parameter_name, parameter_reporter in list(zip(self.parameters, self.parameter_blocks)):
            procedure_prototype_block.set_input_value(parameter_name,
                                                      Input(parameter_reporter, force_input_type=InputType.BLOCK_INPUT),
                                                      ignore_safety=True)

        final_data = {}

        if self.current_block_stack and not self.current_block_stack.empty():
            self.current_block_stack.first_block.connect_parent(procedure_definition_block, auto_set_child=True)
            for block_id, block_data in self.current_block_stack.generate_data().items():
                final_data[block_id] = block_data

        for block in self.unordered_blocks:
            final_data[block.uuid] = block.generate_data()

        for parameter_block in self.parameter_blocks:
            final_data[parameter_block.uuid] = parameter_block.generate_data()

        final_data[procedure_prototype_block.uuid] = prototype_block_data
        final_data[procedure_definition_block.uuid] = procedure_definition_block.generate_data()

        return final_data
