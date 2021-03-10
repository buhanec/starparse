"""Basic config."""

import os

__all__ = ('UTF8', 'BYTE_STRUCT', 'ORDERED_DICT')


def _bool(env_var: str, default: bool) -> bool:
    if env_var not in os.environ:
        return default
    return os.environ[env_var].upper() in ('1', 'T', 'TRUE')


UTF8 = _bool('STARPARSE_UTF8', False)
BYTE_STRUCT = _bool('STARPARSE_BYTE_STRUCT', False)
ORDERED_DICT = _bool('STARPARSE_ORDERED_DICT', True)
