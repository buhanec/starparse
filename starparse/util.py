"""Utility functions."""

import logging
from typing import Any

__all__ = ('diff',)

logger = logging.getLogger(__name__)


def diff(a: Any, b: Any, context: str) -> int:
    """
    Diff two values.

    :param a: First value
    :param b: Second value
    :param context: Context placing the values relative to root values
    :return: Count of diffs
    """
    if isinstance(a, dict) and isinstance(b, dict):
        return _dict_diff(a, b, context=context)
    if isinstance(a, list) and isinstance(b, list):
        return _list_diff(a, b, context=context)
    return _generic_diff(a, b, context=context)


def _dict_diff(a: Any, b: Any, context: str = 'base') -> int:
    a_extra = a.keys() - b.keys()
    b_extra = b.keys() - a.keys()
    diffs = 0
    if a_extra:
        logger.warning(context)
        logger.warning('  extra keys in a: %s', a_extra)
        diffs += len(a_extra)
    if b_extra:
        logger.warning(context)
        logger.warning('  extra keys in b: %s', b_extra)
        diffs += len(b_extra)
    for k in a.keys() & b.keys():
        diffs += diff(a[k], b[k], context + '.' + k)
    return diffs


def _list_diff(a: Any, b: Any, context: str = 'base') -> int:
    if len(a) != len(b):
        logger.warning(context)
        logger.warning('  list len mismatch: %d, %d', len(a), len(b))
        return max(len(a), len(b))
    diffs = 0
    for i, va, vb in zip(map(str, range(len(a))), a, b):
        diffs += diff(va, vb, context + '[' + i + ']')
    return diffs


def _generic_diff(a: Any, b: Any, context: str = 'base') -> int:
    if a != b:
        logger.warning(context)
        logger.warning('  generic mismatch')
        logger.warning('  %s (%s)', a, type(a).__name__)
        logger.warning('  %s (%s)', b, type(b).__name__)
        return 1
    return 0
