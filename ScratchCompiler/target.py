from hashlib import md5
import os

from .blocks import BlockStack
from .exceptions import ScratchCompilerException


def generate_md5(path: str) -> str:
    with open(path, "rb") as image_file:
        return md5(image_file.read()).hexdigest()


class Costume:
    def __init__(self, file_path: str, data_format: str, name: str, bitmap_resolution: int = 1,
                 px_pivot: (float, float) = (0, 0)):
        md5_str = generate_md5(file_path)

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
        with open(os.path.join(output_dir_path, self.costume_data['md5ext']), "wb") as write_to:
            with open(self.original_file_path, "rb") as read_from:
                write_to.write(read_from.read())


class Sound:
    def __init__(self, file_path: str, data_format: str, name: str, rate: int = 44100, sample_count: int = 1032):
        md5_str = generate_md5(file_path)

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
    def __init__(self, name: str = "Sprite"):
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
        blocks_data = block_stack.generate_data()

        if len(blocks_data) < 1:
            return

        for block_uuid, block_data in blocks_data.items():
            self.sprite_data["blocks"][block_uuid] = block_data

    def create_variable(self, var_id: str, default_value: str | int = 0):
        self.sprite_data["variables"][var_id] = [
            var_id,
            default_value
        ]

    def add_costume(self, costume: Costume):
        self.costume_objects.append(costume)
        self.sprite_data["costumes"].append(costume.costume_data)

    def set_property(self, sprite_property: str, value: int | str | bool):
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
