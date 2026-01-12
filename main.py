import os

import tests
from ScratchCompiler.sb3_project import build_sb3_from_project

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
BUILD_FOLDER_PATH = os.path.join(SCRIPT_PATH, "build")
TEMP_FOLDER_PATH = os.path.join(BUILD_FOLDER_PATH, "temp")
OUTPUT_FOLDER_PATH = os.path.join(BUILD_FOLDER_PATH, "output")


def main():
    project = tests.control_test()
    build_sb3_from_project(project, "project_result", temp_folder_path=TEMP_FOLDER_PATH,
                           output_folder_path=OUTPUT_FOLDER_PATH)


if __name__ == "__main__":
    main()
