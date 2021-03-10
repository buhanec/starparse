"""Unpacking functionality."""

from collections import OrderedDict
from struct import calcsize, unpack_from
from typing import Any, Dict, List, Tuple, Union

from starparse import config

__all__ = ('UnpackingError', 'struct', 'uint', 'int_', 'str_', 'bool_',
           'none', 'float_', 'type_', 'list_', 'dict_', 'typed', 'header')

SBT = Union[None, str, int, float, list, dict, OrderedDict]


class UnpackingError(Exception):
    """Unpacking error."""


def struct(fmt: str, buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
    """
    Unpack struct from Starbound save file.

    :param fmt: struct format
    :param buffer: Starbound save file
    :param offset: Starbound save file format
    :return: data, new offset
    :raises UnpackingError: when format not as expected
    """
    unpacked = unpack_from(fmt, buffer, offset)
    offset += calcsize(fmt)

    # Unpacking string, join all bytes and decode
    if all(isinstance(b, bytes) for b in unpacked):
        try:
            result = b''.join(unpacked).decode('ascii')
        except UnicodeDecodeError as e:
            if config.UTF8:
                result = b''.join(unpacked).decode('utf-8')
            else:
                raise UnpackingError(f'ASCII decoding error {unpacked}') from e
        return result, offset

    # Single type (float, int, ...)
    if len(unpacked) == 1:
        return unpacked[0], offset

    raise UnpackingError('Multiple non-bytes in bytearray')


def uint(buffer: bytes, offset: int = 0) -> Tuple[int, int]:
    """
    Unpack unsigned int from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: unsigned int, new offset
    """
    value = 0
    while True:
        tmp = buffer[offset]
        value = (value << 7) | (tmp & 127)
        offset += 1
        if not tmp & 128:
            break
    return value, offset


def int_(buffer: bytes, offset: int = 0) -> Tuple[int, int]:
    """
    Unpack signed int from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: int, new offset
    """
    value = 0
    while True:
        tmp = buffer[offset]
        value = (value << 7) | (tmp & 127)
        offset += 1
        if not tmp & 128:
            break
    if value & 1:
        value = -((value >> 1) + 1)
    else:
        value >>= 1
    return value, offset


def str_(buffer: bytes, offset: int = 0) -> Tuple[str, int]:
    """
    Unpack str from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: str, new offset
    """
    length, offset = uint(buffer, offset)
    fmt = '{0:d}c'.format(length)
    return struct(fmt, buffer, offset)


def bool_(buffer: bytes, offset: int = 0) -> Tuple[bool, int]:
    """
    Unpack bool from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: bool, new offset
    """
    return bool(buffer[offset]), offset + 1


# pylint: disable=unused-argument
# noinspection PyUnusedLocal
def none(buffer: bytes, offset: int = 0) -> Tuple[None, int]:
    """
    Unpack None/unset from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: None, new offset
    """
    return None, offset


def float_(buffer: bytes, offset: int = 0) -> Tuple[float, int]:
    """
    Unpack float from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: float, new offset
    """
    return struct('>d', buffer, offset)


def type_(buffer: bytes, offset: int = 0) -> Tuple[type, int]:
    """
    Unpack type from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: type, new offset
    :raises UnpackingError: when format not as expected
    """
    types = [type(None), float, bool, int, str, list, dict]
    index, offset = uint(buffer, offset)
    if index > len(types):
        raise UnpackingError(f'Unsupported value type: {index}')
    return types[index - 1], offset


def list_(buffer: bytes, offset: int = 0) -> Tuple[List[SBT], int]:
    """
    Unpack list from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: list, new offset
    """
    length, offset = uint(buffer, offset)
    result = []
    for _ in range(length):
        item, offset = typed(buffer, offset)
        result.append(item)
    return result, offset


def dict_(buffer: bytes, offset: int = 0) -> Tuple[Dict[str, SBT], int]:
    """
    Unpack dict from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: dict, new offset
    """
    length, offset = uint(buffer, offset)

    result: Dict[str, SBT]
    if config.ORDERED_DICT:
        result = OrderedDict()
    else:
        result = {}

    for _ in range(length):
        key, offset = str_(buffer, offset)
        item, offset = typed(buffer, offset)
        result[key] = item

    return result, offset


def typed(buffer: bytes, offset: int = 0) -> Tuple[SBT, int]:
    """
    Unpack a typed data structure from the buffer at a given offset.

    :param buffer: buffer to read
    :param offset: offset in buffer
    :return: unpacked data
    """
    handlers = {
        type(None): none,
        bool: bool_,
        int: int_,
        float: float_,
        list: list_,
        dict: dict_,
        str: str_
    }
    value_type, offset = type_(buffer, offset)
    value, offset = handlers[value_type](buffer, offset)
    return value, offset


def header(buffer: bytes, offset: int = 0) -> Tuple[bytes, str, List[int], int]:
    """
    Unpack a Starbound header structure from the buffer at a given offset.

    :param buffer: buffer to read
    :param offset: offset in buffer
    :return: Starbound header
    """
    save_format = buffer[offset:offset + 6]
    offset += 6
    entity, offset = str_(buffer, offset=offset)
    flags = list(buffer[offset:offset + 5])
    offset += 5
    return save_format, entity, flags, offset
