from importlib.resources import read_binary
import itertools

import pytest

from starparse import config, pack, unpack
from tests import ci_players


@pytest.mark.parametrize('player, ordered_dict',
                         itertools.product(ci_players.PLAYERS, (True, False)))
def test_unordered(player, ordered_dict, monkeypatch):
    monkeypatch.setattr(config, 'ORDERED_DICT', ordered_dict)
    file = read_binary(ci_players, f'{player}.player')

    # Unpack
    save_format, entity, flags, offset = unpack.header(file, 0)
    unpacked, limit = unpack.typed(file, offset)

    assert limit == len(file)
    assert save_format == b'SBVJ01'

    # Pack
    packed = pack.header(save_format, entity, flags) + pack.typed(unpacked)

    assert len(packed) == len(file)

    # Re-unpack
    save_format_2, entity_2, flags_2, offset_2 = unpack.header(packed, 0)
    unpacked_2, limit_2 = unpack.typed(packed, offset_2)
    assert save_format == save_format_2
    assert entity == entity_2
    assert flags == flags_2
    assert offset == offset_2
    assert limit == limit_2
    assert unpacked == unpacked_2

    if ordered_dict:
        assert packed == file
