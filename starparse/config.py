"""Basic config."""

import os

__all__ = ('UTF8', 'ORDERED_DICT')


def _bool(env_var: str, default: bool) -> bool:
    if env_var not in os.environ:
        return default
    return os.environ[env_var].upper() in ('1', 'T', 'TRUE')


UTF8 = _bool('STARPARSE_UTF8', False)
ORDERED_DICT = _bool('STARPARSE_ORDERED_DICT', True)
