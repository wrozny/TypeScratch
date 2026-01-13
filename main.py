import os

import tests
from ScratchCompiler.sb3_project import build_sb3_from_project

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
BUILD_FOLDER_PATH = os.path.join(SCRIPT_PATH, "build")
TEMP_FOLDER_PATH = os.path.join(BUILD_FOLDER_PATH, "temp")
OUTPUT_FOLDER_PATH = os.path.join(BUILD_FOLDER_PATH, "output")


def main():
    """
        Here we create a project from the tests.py and build an .sb3 file
        the file can be found in the working directory under:
        .../build/output/project_result.sb3

        the project variable can also be changed to:
        project = tests.fields_test()
        project = tests.inputs_test()
    """
    project = tests.control_test()
    build_sb3_from_project(project, "project_result", temp_folder_path=TEMP_FOLDER_PATH,
                           output_folder_path=OUTPUT_FOLDER_PATH)


if __name__ == "__main__":
    main()
