from string import ascii_letters, digits
from collections.abc import Generator

BASE62_CHARACTERS = digits + ascii_letters


def encode_base62(number: int) -> str:
    """
    Encodes a number in base 62 (all digits 0-9 and letters a-Z)
    :param number: number to encode
    :return: Encoded base62 string
    """

    if number == 0:
        return BASE62_CHARACTERS[0]

    result = ""

    while number > 0:
        number, remainder = divmod(number, 62)
        result = BASE62_CHARACTERS[remainder] + result

    return result


def get_unique_mangle_id_generator() -> Generator[str, None, None]:
    """
    Creates a new generator function that yields unique base62 encoded number every call for mangling
    :return: Mangle id generator
    """
    current_num = 0
    while True:
        yield encode_base62(current_num)
        current_num += 1
