"""Unpacking functionality."""

from collections import OrderedDict
import logging
from struct import calcsize, unpack_from
from typing import Any, Dict, List, Optional, Tuple, Union

from starparse import config

logger = logging.getLogger(__name__)

SBT = Union[str, int, float, list, dict, OrderedDict]


class UnpackingError(Exception):
    """Unpacking error."""


def struct(fmt: str, buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
    """
    Unpack struct from Starbound save file.

    :param fmt: struct format
    :param buffer: Starbound save file
    :param offset: Starbound save file format
    :return: data, new offset
    """
    result = unpack_from(fmt, buffer, offset)
    offset += calcsize(fmt)
    if all(isinstance(b, bytes) for b in result):
        try:
            result = b''.join(result).decode('ascii')
        except UnicodeDecodeError:
            error = 'ASCII decoding error {0}'.format(result)
            if config.UTF8:
                result = b''.join(result).decode('utf-8')
                logging.warning('%d | struct %s', offset, error)
            else:
                logging.exception('%d | struct %s', offset, error)
                raise UnpackingError(error)
    elif len(result) == 1:
        result = result[0]
    elif not config.BYTE_STRUCT:
        error = 'Multiple non-bytes in bytearray'
        logging.exception('%d | struct %s', error)
        raise UnpackingError(error)
    return result, offset


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


def type_(buffer: bytes, offset: int = 0) -> Tuple[Optional[type], int]:
    """
    Unpack type from Starbound save file.

    :param buffer: Starbound save file
    :param offset: position in Starbound save file
    :return: type, new offset
    """
    types = [None, float, bool, int, str, list, dict]
    index, offset = uint(buffer, offset)
    try:
        return types[index - 1], offset
    except IndexError:
        error = 'unsupported value type: {0}'.format(index)
        logger.exception('%d | type -> %s', offset, error)
        raise UnpackingError(error)


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
    handlers = {
        None: none,
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
    save_format = buffer[offset:offset + 6]
    offset += 6
    entity, offset = str_(buffer, offset=offset)
    flags = list(buffer[offset:offset + 5])
    offset += 5
    return save_format, entity, flags, offset
