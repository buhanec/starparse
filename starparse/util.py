import logging
logger = logging.getLogger(__name__)


def diff(a, b, context):
    if isinstance(a, dict) and isinstance(b, dict):
        return dict_diff(a, b, context=context)
    elif isinstance(a, list) and isinstance(b, list):
        return list_diff(a, b, context=context)
    else:
        return generic_diff(a, b, context=context)


def dict_diff(a, b, context='base'):
    a_extra = a.keys() - b.keys()
    b_extra = b.keys() - a.keys()
    diffs = 0
    if a_extra:
        logger.warn(context)
        logger.warn('  extra keys in a: %s', a_extra)
        diffs += len(a_extra)
    if b_extra:
        logger.warn(context)
        logger.warn('  extra keys in b: %s', b_extra)
        diffs += len(b_extra)
    for k in a.keys() & b.keys():
        diffs += diff(a[k], b[k], context + '.' + k)
    return diffs


def list_diff(a, b, context='base'):
    if len(a) != len(b):
        logger.warn(context)
        logger.warn('  list len mismatch: %d, %d', len(a), len(b))
        return max(len(a), len(b))
    diffs = 0
    for i, va, vb in zip(map(str, range(len(a))), a, b):
        diffs += diff(va, vb, context + '[' + i + ']')
    return diffs


def generic_diff(a, b, context='base'):
    if a != b:
        logger.warn(context)
        logger.warn('  generic mismatch')
        logger.warn('  %s (%s)', a, type(a).__name__)
        logger.warn('  %s (%s)', b, type(b).__name__)
        return 1
    return 0
