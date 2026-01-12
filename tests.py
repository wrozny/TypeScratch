import os

from ScratchCompiler import target, sb3_project, blocks

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
BUILD_FOLDER = os.path.join(SCRIPT_PATH, "build")
TEMP_FOLDER = os.path.join(BUILD_FOLDER, "temp")
OUTPUT_FOLDER = os.path.join(BUILD_FOLDER, "output")

ducky_costume = target.Costume(
    file_path="assets/ducky.png",
    data_format="png",
    name="DuckyIdle",
    px_pivot=(16, 16),
    bitmap_resolution=1
)

empty_background = target.Costume(
    file_path="assets/empty_background.svg",
    data_format="svg",
    name="EMPTY_BACKGROUND",
    px_pivot=(0, 0),
    bitmap_resolution=1
)


def inputs_test() -> sb3_project.Project:
    stage = target.Stage()
    stage.add_costume(empty_background)
    stage.create_variable(var_id="GLOBAL_VAR", default_value="120")

    sprite = target.Sprite(name="Ducky")
    sprite.add_costume(ducky_costume)
    sprite.create_variable(var_id="LOCAL_VAR", default_value=340)

    project_start_definition = blocks.Definitions.WHEN_FLAG_CLICKED
    move_forward_definition = blocks.Definitions.MOVE_STEPS
    goto_definition = blocks.Definitions.GOTO_XY

    start_block = blocks.Block(project_start_definition)

    motion_block = blocks.Block(move_forward_definition)
    motion_block.set_input_value("STEPS", blocks.Input("10"))

    goto_block = blocks.Block(goto_definition)
    goto_block.set_input_value("X", blocks.Input(blocks.VariableReference("LOCAL_VAR")))
    goto_block.set_input_value("Y", blocks.Input("2"))

    block_stack = blocks.BlockStack()
    block_stack.add_block(start_block)
    block_stack.add_block(motion_block)
    block_stack.add_block(goto_block)

    sprite.add_block_stack(block_stack)

    project = sb3_project.Project()
    project.add_sprite(stage)
    project.add_sprite(sprite)

    return project


def fields_test() -> sb3_project.Project:
    stage = target.Stage()
    stage.add_costume(empty_background)

    sprite = target.Sprite(name="Ducky")
    sprite.add_costume(ducky_costume)
    sprite.set_property("draggable", True)

    sprite.create_variable("step_size", 15)

    start_block = blocks.Block(blocks.Definitions.WHEN_FLAG_CLICKED)

    step_size_setter = blocks.Block(blocks.Definitions.SET_VARIABLE_TO)
    step_size_setter.set_input_value("VALUE", blocks.Input("30"))
    step_size_setter.set_field_value("VARIABLE",
                                     blocks.FieldInput(blocks.VariableReference("step_size", is_field_selector=True)))

    add_block = blocks.Block(blocks.Definitions.MATH_ADD)
    add_block.set_input_value("NUM1", blocks.Input("10"))
    add_block.set_input_value("NUM2", blocks.Input(blocks.VariableReference("step_size")))

    move_steps_block = blocks.Block(blocks.Definitions.MOVE_STEPS)
    move_steps_block.set_input_value("STEPS", blocks.Input(add_block))

    block_stack = blocks.BlockStack()
    block_stack.add_block(start_block)
    block_stack.add_block(step_size_setter)
    block_stack.add_block(move_steps_block)

    block_stack.add_block(add_block, auto_parent=False)

    sprite.add_block_stack(block_stack)

    project = sb3_project.Project()
    project.add_sprite(stage)
    project.add_sprite(sprite)

    return project


def control_test() -> sb3_project.Project:
    stage = target.Stage()
    stage.add_costume(empty_background)

    ducky = target.Sprite(name="Ducky")
    ducky.add_costume(ducky_costume)

    main_block_stack = blocks.BlockStack()

    start_block = blocks.Block(blocks.Definitions.WHEN_FLAG_CLICKED)
    main_block_stack.add_block(start_block)

    ducky.create_variable("duck_age", 1)

    age_increment_block = blocks.Block(blocks.Definitions.MATH_ADD)
    age_increment_block.set_input_value("NUM1", blocks.Input(blocks.VariableReference("duck_age")))
    age_increment_block.set_input_value("NUM2", blocks.Input("1"))

    setter_block = blocks.Block(blocks.Definitions.SET_VARIABLE_TO)
    setter_block.set_field_value("VARIABLE",
                                 blocks.FieldInput(blocks.VariableReference("duck_age", is_field_selector=True)))
    setter_block.set_input_value("VALUE", blocks.Input(age_increment_block))

    main_block_stack.add_block(setter_block)
    main_block_stack.add_block(age_increment_block, auto_parent=False)

    block_substack = blocks.BlockStack()

    resize_block = blocks.Block(blocks.Definitions.LOOKS_SET_SIZE_TO)
    resize_block.set_input_value("SIZE", blocks.Input(blocks.VariableReference("duck_age")))

    block_substack.add_block(resize_block)

    age_check = blocks.Block(blocks.Definitions.OPERATOR_GT)
    age_check.set_input_value("OPERAND1", blocks.Input(blocks.VariableReference("duck_age")))
    age_check.set_input_value("OPERAND2", blocks.Input("10"))

    first_if = blocks.Block(blocks.Definitions.CONTROL_IF)
    first_if.set_input_value("CONDITION", blocks.Input(age_check))
    first_if.set_input_value("SUBSTACK", blocks.Input(resize_block))
    main_block_stack.add_block(first_if)
    main_block_stack.add_block(age_check, auto_parent=False)

    project = sb3_project.Project()

    ducky.add_block_stack(block_substack)
    ducky.add_block_stack(main_block_stack)

    project.add_sprite(stage)
    project.add_sprite(ducky)

    return project
