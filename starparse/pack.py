from typing import Union, Dict, Any, List
from struct import pack
from collections import OrderedDict
from functools import wraps
from starparse import config
import logging
logger = logging.getLogger(__name__)


SBT = Union[str, int, float, list, dict, OrderedDict]


class PackingError(Exception):

    """Packing error."""


def coerce(f):
    @wraps(f)
    def wrapper(value):
        expecting = f.__annotations__['value']
        if expecting.__name__ == 'List':
            expecting = list
        elif expecting.__name__ == 'Dict':
            if config.ORDERED_DICT:
                expecting = OrderedDict
            else:
                expecting = dict
        if not isinstance(value, expecting):
            logging.error('%s.%s expecting %s but got %s: %s',
                          f.__module__, f.__name__,
                          expecting.__name__, type(value).__name__, value)
            value = expecting(value)
        return f(value)
    return wrapper


def optional_arg_decorator(fn):
    def wrapped_decorator(*args):
        if len(args) == 1 and callable(args[0]):
            return fn(args[0])
        else:
            def real_decorator(decorate):
                return fn(decorate, *args)
            return real_decorator
    return wrapped_decorator


@coerce
def uint(value: int) -> bytearray:
    """
    Pack type to Starbound format.
    :param value: unsigned int
    :return: bytearray
    """
    if value < 0:
        error = 'unsigned int cannot be negative: {0}'.format(value)
        logging.exception(error)
        raise PackingError(error)
    result = bytearray()
    result.insert(0, value & 127)
    value >>= 7
    while value:
        result.insert(0, value & 127 | 128)
        value >>= 7
    return result


@coerce
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


@coerce
def str_(value: str) -> bytearray:
    """
    Pack string to Starbound format.
    :param value: string
    :return: bytearray
    """
    result = uint(len(value))
    try:
        result.extend(bytearray(value, 'ascii'))
    except UnicodeEncodeError:
        error = 'string ASCII encoding error: {0}'.format(value)
        if config.UTF8:
            logging.warning(error)
            result.extend(bytearray(value, 'utf-8'))
        else:
            logging.exception(error)
            raise PackingError(error)
    return result


@coerce
def bool_(value: bool) -> bytearray:
    """
    Pack bool to Starbound format.
    :param value: bool
    :return: bytearray
    """
    return bytearray([value])


# noinspection PyUnusedLocal
def none(value: Any=None) -> bytearray:
    """
    Pack None/unset to Starbound format.
    :param value: unused
    :return: bytearray
    """
    return bytearray()


@coerce
def float_(value: float) -> bytearray:
    """
    Pack float to Starbound format.
    :param value: float
    :return: bytearray
    """
    return pack('>d', value)


def type_(value: type) -> bytearray:
    """
    Pack type to Starbound format.
    :param value: type
    :return: bytearray
    """
    types = dict(zip((type(None), float, bool, int, str, list, dict),
                     range(1, 8)))
    types[OrderedDict] = types[dict]
    try:
        return uint(types[value])
    except KeyError:
        error = 'unsupported value type: {0}'.format(value)
        logger.exception(error)
        raise PackingError(error)


@coerce
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


@coerce
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
    handlers = {
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
    return bytearray(save_format) + str_(entity) + bytearray(flags)