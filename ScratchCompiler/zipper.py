import os
import zipfile


def zip_files(file_paths: [str], output_path: str):
    """
    Creates a zip out of provided files
    :param file_paths: List of paths to a file
    :param output_path: Path to the directory where result will be saved
    """
    with zipfile.ZipFile(output_path, 'w') as zip_file:
        for file in file_paths:
            zip_file.write(file, os.path.basename(file))


def unzip_files(archive_path: str, output_dir: str):
    """
    Unpacks a zip archive
    :param archive_path: Path to the archive
    :param output_dir: Path where to unpack
    :return:
    """

    if not (os.path.exists(output_dir) or os.path.exists(archive_path)):
        raise FileNotFoundError(f"Output directory or archive doesn't exist!")

    with zipfile.ZipFile(archive_path, 'r') as zip_file:
        zip_file.extractall(output_dir)
