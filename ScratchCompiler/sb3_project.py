from .target import *
from .zipper import zip_files
import json
import os

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
BUILD_FOLDER_PATH = os.path.join(SCRIPT_PATH, "build")
TEMP_FOLDER_PATH = os.path.join(BUILD_FOLDER_PATH, "temp")
OUTPUT_FOLDER_PATH = os.path.join(BUILD_FOLDER_PATH, "output")


def ensure_folders_exist(*folder_paths: str):
    """
    Checks if each path goes to a folder and if it doesn't, makes one.
    :param folder_paths: paths of folders
    """
    for folder_path in folder_paths:
        os.makedirs(folder_path, exist_ok=True)


class Project:
    """
        Abstraction of the project.json file from .sb3 format
    """
    def __init__(self):
        self.sprite_objects = []
        self.project_data = {
            "targets": [],
            "monitors": [],
            "extensions": [],
            "meta": {
                "semver": "3.0.0",
                "vm": "0.2.0-prerelease.20220222132735",
                "agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Scratch/3.29.1 Chrome/94.0.4606.81 Electron/15.3.1 Safari/537.36"
            }
        }

    def add_sprite(self, sprite: Sprite):
        """
        Adds new sprite to the project
        :param sprite: Sprite object
        """
        self.sprite_objects.append(sprite)
        self.project_data["targets"].append(sprite.sprite_data)

    def build_project_data(self, temp_dir_path: str):
        """
        Writes the project.json and all used resources in a temporary folder for zipping
        :param temp_dir_path: Path to a temporary folder
        """
        for sprite in self.sprite_objects:
            for costume in sprite.costume_objects:
                costume.save_hashed_image(output_dir_path=temp_dir_path)

        with open(os.path.join(temp_dir_path, "project.json"), "w") as project_file:
            json.dump(self.project_data, project_file)


def build_sb3_from_project(project: Project, project_name: str = "project", temp_folder_path: str = TEMP_FOLDER_PATH, output_folder_path: str = OUTPUT_FOLDER_PATH):
    """
    Creates the .sb3 file from Project object
    :param project: The Project object
    :param project_name: Name of the final file
    :param temp_folder_path: Path to a temporary folder
    :param output_folder_path: Path to a folder where .sb3 file will be saved
    """
    ensure_folders_exist(temp_folder_path, output_folder_path)
    project.build_project_data(temp_dir_path=temp_folder_path)
    file_paths = map(lambda basename: os.path.join(temp_folder_path, basename), os.listdir(temp_folder_path))
    zip_files(file_paths=file_paths, output_path=os.path.join(output_folder_path, f"{project_name}.sb3"))
