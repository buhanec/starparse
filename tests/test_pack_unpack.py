from collections import OrderedDict
import math
from string import printable
from typing import Any, Dict, List, TYPE_CHECKING

from hypothesis import example, given
from hypothesis.strategies import floats, integers, text
import pytest

from starparse import config, pack, unpack

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 9):
        OrderedDict_ = OrderedDict
    elif sys.version_info >= (3, 7, 2):
        from typing import OrderedDict as OrderedDict_
    else:
        OrderedDict_ = Dict


def parity(packer, unpacker, reference, asserter, packed_reference=None):
    packed = packer(reference)
    if packed_reference is not None:
        asserter(packed, packed_reference)
    unpacked, _ = unpacker(packed)
    asserter(unpacked, reference)


@pytest.mark.parametrize('args, expected', [
    (('4c', b'Alen'), ('Alen', 4)),
    (('4c', b'Alen B'), ('Alen', 4)),
    (('2c', b'Alen B', 2), ('en', 4)),
    (('b', b'\x01\xFF'), (1, 1)),
    (('b', b'\x00\xFF'), (0, 1)),
    (('<i', b'\x00\x88\x00\x00'), (34816, 4))
])
def test_struct(args, expected):
    assert unpack.struct(*args) == expected


@given(n=integers(min_value=0, max_value=2 ** 256))
def test_uint(n):
    packed = pack.uint(n)
    unpacked, offset = unpack.uint(packed)
    assert offset == len(packed)
    assert unpacked == n


@given(n=integers(min_value=-(2 ** 127), max_value=2 ** 127 - 1))
def test_int(n: int):
    packed = pack.int_(n)
    unpacked, offset = unpack.int_(packed)
    assert offset == len(packed)
    assert unpacked == n


@given(string=text(alphabet=printable))
@example(string=printable)
def test_str(string: str):
    packed = pack.str_(string)
    unpacked, offset = unpack.str_(packed)
    assert offset == len(packed)
    assert unpacked == string


@pytest.mark.parametrize('value', [True, False])
def test_bool(value: bool):
    packed = pack.bool_(value)
    unpacked, offset = unpack.bool_(packed)
    assert offset == len(packed)
    assert unpacked == value


def test_none():
    packed = pack.none(None)
    unpacked, offset = unpack.none(packed)
    assert offset == len(packed)
    assert unpacked is None


@pytest.mark.parametrize('n', [-float('nan'), float('nan')])
def test_float_nan(n: float):
    packed = pack.float_(n)
    unpacked, offset = unpack.float_(packed)
    assert offset == len(packed)
    assert math.isnan(unpacked)
    assert math.copysign(1.0, unpacked) == math.copysign(1.0, n)


@pytest.mark.parametrize('n', [-float('nan'), float('nan')])
def test_float_nan(n: float):
    packed = pack.float_(n)
    unpacked, offset = unpack.float_(packed)
    assert offset == len(packed)
    assert math.isnan(unpacked)
    assert math.copysign(1.0, unpacked) == math.copysign(1.0, n)


@given(n=floats(allow_nan=False))
@example(n=float('inf'))
@example(n=-float('inf'))
def test_float(n: float):
    packed = pack.float_(n)
    unpacked, offset = unpack.float_(packed)
    assert offset == len(packed)
    assert unpacked == n


@pytest.mark.parametrize('packed, expected', [
    (b'\x01', type(None)),
    (b'\x02', float),
    (b'\x03', bool),
    (b'\x04', int),
    (b'\x05', str),
    (b'\x06', list),
    (b'\x07', dict),
])
def test_types(packed: bytes, expected: Any, monkeypatch):
    unpacked, offset = unpack.type_(packed)
    assert offset == len(packed)
    assert unpacked == expected


@pytest.mark.parametrize('value', [
    [],
    [1, 2, 3],
    ["a", "b", "c"],
    [1, "b", []],
    [1, "b", [1, "c"]],
])
def test_list(value: List[Any]):
    packed = pack.list_(value)
    unpacked, offset = unpack.list_(packed)
    assert offset == len(packed)
    assert unpacked == value


@pytest.mark.parametrize('value', [
    {},
    {"a": 1, "b": 2},
    {"a": "a", "b": 2},
    {"a": {"b": {}}},
])
def test_dict(value: Dict[Any, Any], monkeypatch):
    monkeypatch.setattr(config, 'ORDERED_DICT', False)

    packed = pack.dict_(value)
    unpacked, offset = unpack.dict_(packed)
    assert offset == len(packed)
    assert unpacked == value


@pytest.mark.parametrize('value', [
    OrderedDict({}),
    OrderedDict({"a": 1, "b": 2}),
    OrderedDict({"a": "a", "b": 2}),
    OrderedDict({"a": OrderedDict({"b": OrderedDict({})})}),
])
def test_dict_ordered(value: 'OrderedDict_[Any, Any]', monkeypatch):
    monkeypatch.setattr(config, 'ORDERED_DICT', True)

    packed = pack.dict_(value)
    unpacked, offset = unpack.dict_(packed)
    assert offset == len(packed)
    assert unpacked == value
