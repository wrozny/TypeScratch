from hashlib import md5
import os

from .blocks import BlockStack
from .exceptions import ScratchCompilerException


def generate_md5_hash(file_path: str) -> str:
    """
    Generates md5 hash from a file
    :param file_path: File path to an image to be hashed
    :return: md5 hash as a string
    """
    with open(file_path, "rb") as image_file:
        return md5(image_file.read()).hexdigest()


class Costume:
    """
        Abstraction of the scratch costume data
    """
    def __init__(self, file_path: str, data_format: str, name: str, bitmap_resolution: int = 1,
                 px_pivot: (float, float) = (0, 0)):
        """
        :param file_path: Path to the costume image
        :param data_format: Format of the image
        :param name: Name of the costume to be used
        :param bitmap_resolution: The resolution of an image, 2 meaning half of the resolution. (keep it at 1 for convenience)
        :param px_pivot: The offset from the image top left corner determining point from where position is calculated in scratch
        """
        md5_str = generate_md5_hash(file_path)

        self.original_file_path = file_path
        self.costume_data = {
            "assetId": md5_str,
            "name": name,
            "bitmapResolution": bitmap_resolution,
            "md5ext": f"{md5_str}.{data_format}",
            "dataFormat": data_format,
            "rotationCenterX": px_pivot[0],
            "rotationCenterY": px_pivot[1]
        }

    def save_hashed_image(self, output_dir_path: str):
        """
        Saves the hashed image inside output directory
        :param output_dir_path: The directory path
        """
        with open(os.path.join(output_dir_path, self.costume_data['md5ext']), "wb") as write_to:
            with open(self.original_file_path, "rb") as read_from:
                write_to.write(read_from.read())


class Sound:
    """
        Abstraction of the scratch sound data
        NOT IMPLEMENTED YET!
    """
    def __init__(self, file_path: str, data_format: str, name: str, rate: int = 44100, sample_count: int = 1032):
        """
        TODO!!!
        :param file_path:
        :param data_format:
        :param name:
        :param rate:
        :param sample_count:
        """
        md5_str = generate_md5_hash(file_path)

        self.original_file_path = file_path
        self.sound_data = {
            "assetId": md5_str,
            "name": name,
            "dataFormat": data_format,
            "format": "",
            "rate": rate,
            "sampleCount": sample_count,
            "md5ext": f"{md5_str}.{data_format}"
        }

    def save_hashed_sound(self, output_dir_path: str):
        with open(os.path.join(output_dir_path, self.sound_data['md5ext']), "wb") as write_to:
            with open(self.original_file_path, "rb") as read_from:
                write_to.write(read_from.read())


class Sprite:
    """
        Abstraction of the scratch sprite data
    """
    def __init__(self, name: str = "Sprite"):
        """
        :param name: Name of the sprite
        """
        self.costume_objects = []
        self.sprite_data = {
            "isStage": False,
            "name": name,
            "variables": {},
            "lists": {},
            "broadcasts": {},
            "blocks": {},
            "comments": {},
            "currentCostume": 0,
            "costumes": [],
            "sounds": [],
            "volume": 100,
            "layerOrder": 1,
            "visible": True,
            "x": 0,
            "y": 0,
            "size": 100,
            "direction": 90,
            "draggable": False,
            "rotationStyle": "all around"
        }

    def add_block_stack(self, block_stack: BlockStack) -> None:
        """
        Saves every block data from a block stack
        :param block_stack: The block stack
        """
        blocks_data = block_stack.generate_data()

        if len(blocks_data) < 1:
            return

        for block_uuid, block_data in blocks_data.items():
            self.sprite_data["blocks"][block_uuid] = block_data

    def create_variable(self, var_id: str, default_value: str | int = 0):
        """
        Defines a local variable in sprite memory
        :param var_id: ID of the variable to be referenced
        :param default_value: Value set at initial state of project
        """
        self.sprite_data["variables"][var_id] = [
            var_id,
            default_value
        ]

    def add_costume(self, costume: Costume):
        """
        Adds new costume to the sprite
        :param costume: Costume object
        """
        self.costume_objects.append(costume)
        self.sprite_data["costumes"].append(costume.costume_data)

    def set_property(self, sprite_property: str, value: int | str | bool):
        """
        Sets the property of a sprite at initial state of project like "size" or "draggable"
        :param sprite_property: The property to change
        :param value: New value
        """

        if sprite_property == "isStage":
            raise ScratchCompilerException("Property isStage cannot be changed! Use Sprite or Stage class to change this behaviour!")

        current_value = self.sprite_data.get(sprite_property)
        if current_value is None:
            raise ScratchCompilerException(
                f"Property {sprite_property} can't be set because it doesn't exist inside the sprite!")

        if isinstance(current_value, (dict, list)):
            raise ScratchCompilerException(
                f"Property {sprite_property} of a sprite can't be changed because it's a dictionary or list! Only immutable types can be changed!")

        if type(current_value) != type(value):
            raise ScratchCompilerException(
                f"Property {sprite_property} of a sprite can't be changed because invalid type provided, expected '{type(current_value)}' got '{type(value)}'")

        self.sprite_data[sprite_property] = value


class Stage(Sprite):
    """
        Stage abstraction, acts like a sprite but contains different properties
    """
    # noinspection PyMissingConstructor
    def __init__(self):
        self.costume_objects = []
        self.sprite_data = {
            "isStage": True,
            "name": "Stage",
            "variables": {},
            "lists": {},
            "broadcasts": {},
            "blocks": {},
            "comments": {},
            "currentCostume": 0,
            "costumes": [],
            "sounds": [],
            "volume": 100,
            "layerOrder": 0,
            "tempo": 60,
            "videoTransparency": 50,
            "videoState": "on",
            "textToSpeechLanguage": None
        }
