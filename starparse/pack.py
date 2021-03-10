"""Packing functionality."""

from collections import OrderedDict
from functools import wraps
from struct import pack
from typing import Any, Callable, Dict, List, TypeVar, Union

from starparse import config

T = TypeVar('T')
SBT = Union[str, int, float, list, dict, OrderedDict]

__all__ = ('PackingError', 'uint', 'int_', 'str_', 'bool_', 'none',
           'float_', 'type_', 'list_', 'dict_', 'typed', 'header')


class PackingError(Exception):
    """Packing error."""


def check_type(f: Callable[[T], bytearray]) -> Callable[[T], bytearray]:
    """
    Check function argument type.

    :param f: function to check param value for
    :return: function with param value checking
    """
    @wraps(f)
    def wrapper(value):
        expecting = f.__annotations__['value']
        if expecting.__module__ == 'typing' and expecting.__origin__ is list:
            expecting = list
        elif expecting.__module__ == 'typing' and expecting.__origin__ is dict:
            if config.ORDERED_DICT:
                expecting = OrderedDict
            else:
                expecting = dict
        if not isinstance(value, expecting):
            raise TypeError(f'{f.__module__}.{f.__name__} expecting '
                            f'{expecting.__name__} but got '
                            f'{type(value).__name__} ({value!r})')

        return f(value)

    return wrapper


@check_type
def uint(value: int) -> bytearray:
    """
    Pack type to Starbound format.

    :param value: unsigned int
    :return: bytearray
    :raises PackingError: when int negative
    """
    if value < 0:
        raise PackingError(f'unsigned int cannot be negative: {value}')
    result = bytearray()
    result.insert(0, value & 127)
    value >>= 7
    while value:
        result.insert(0, value & 127 | 128)
        value >>= 7
    return result


@check_type
def int_(value: int) -> bytearray:
    """
    Pack int to Starbound format.

    :param value: int
    :return: bytearray
    """
    value_ = abs(value * 2)
    if value < 0:
        value_ -= 1
    return uint(value_)


@check_type
def str_(value: str) -> bytearray:
    """
    Pack string to Starbound format.

    :param value: string
    :return: bytearray
    :raises PackingError: when string encoding error
    """
    result = uint(len(value))
    try:
        result.extend(bytearray(value, 'ascii'))
    except UnicodeEncodeError as e:
        if config.UTF8:
            result.extend(bytearray(value, 'utf-8'))
        else:
            raise PackingError(f'string encoding error: {value!r}') from e
    return result


@check_type
def bool_(value: bool) -> bytearray:
    """
    Pack bool to Starbound format.

    :param value: bool
    :return: bytearray
    """
    return bytearray([value])


# pylint: disable=unused-argument
# noinspection PyUnusedLocal
def none(value: Any = None) -> bytearray:
    """
    Pack None/unset to Starbound format.

    :param value: unused
    :return: bytearray
    """
    return bytearray()


@check_type
def float_(value: float) -> bytearray:
    """
    Pack float to Starbound format.

    :param value: float
    :return: bytearray
    """
    return bytearray(pack('>d', value))


def type_(value: type) -> bytearray:
    """
    Pack type to Starbound format.

    :param value: type
    :return: bytearray
    :raises PackingError: when unsupported value type
    """
    types = dict(zip((type(None), float, bool, int, str, list, dict),
                     range(1, 8)))
    types[OrderedDict] = types[dict]
    try:
        value_type = types[value]
    except KeyError as e:
        raise PackingError(f'unsupported value type: {value}') from e
    return uint(value_type)


@check_type
def list_(value: List[SBT]) -> bytearray:
    """
    Pack list to Starbound format.

    :param value: type
    :return: bytearray
    """
    result = uint(len(value))
    for val in value:
        result.extend(typed(val))
    return result


@check_type
def dict_(value: Dict[str, SBT]) -> bytearray:
    """
    Pack dict to Starbound format.

    :param value: type
    :return: bytearray
    """
    result = uint(len(value))
    for key, val in value.items():
        result.extend(str_(key))
        result.extend(typed(val))
    return result


def typed(value: SBT) -> bytearray:
    """
    Pack type and value to Starbound format.

    :param value: value
    :return: bytearray
    """
    handlers: Dict[type, Callable[[Any], bytearray]] = {
        type(None): none,
        bool: bool_,
        int: int_,
        float: float_,
        list: list_,
        dict: dict_,
        OrderedDict: dict_,
        str: str_
    }
    result = type_(type(value))
    result.extend(handlers[type(value)](value))
    return result


def header(save_format: bytes, entity: str, flags: List[int]) -> bytearray:
    """
    Pack Starbound header to Starbound format.

    :param save_format: save format
    :param entity: entity
    :param flags: flags
    :return: bytearray
    """
    return bytearray(save_format) + str_(entity) + bytearray(flags)
