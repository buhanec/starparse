from unittest import TestCase
from unittest.mock import patch
from collections import OrderedDict
from starparse import pack, unpack
from math import isnan
import random
import string


def parity(packer, unpacker, reference, asserter, packed_reference=None):
    packed = packer(reference)
    if packed_reference is not None:
        asserter(packed, packed_reference)
    unpacked, _ = unpacker(packed)
    asserter(unpacked, reference)


class StructTest(TestCase):
    def test(self):
        cases = [
            (('4c', b'Alen',),              ('Alen',    4)),
            (('4c', b'Alen B',),            ('Alen',    4)),
            (('2c', b'Alen B', 2),          ('en',      4)),
            (('b',  b'\x01\xFF',),          (1,         1)),
            (('b',  b'\x00\xFF',),          (0,         1)),
            (('<i', b'\x00\x88\x00\x00'),   (34816,     4))
        ]
        for args, expected in cases:
            self.assertEqual(unpack.struct(*args), expected)


class UintTest(TestCase):

    def test(self):
        cases = [
            ((b'\xFF\x00',),        (16256, 2)),
            ((b'\x01\xFF',),        (1,     1)),
            ((b'\x00\xFF',),        (0,     1)),
            ((b'A',),               (65,    1)),
            ((b'Alen',),            (65,    1)),
            ((b'\x88\x00',),        (1024,  2)),
            ((b'\x88\x00\x00',),    (1024,  2)),
            ((b'\x01',),            (1,     1)),
            ((b'Alen', 1),          (108,   2)),
            ((b'\x00\x88\x00', 1),  (1024,  3)),
            ((b'\x00\x00\x00', 1),  (0,     2))
        ]
        for args, expected in cases:
            self.assertEqual(unpack.uint(*args), expected)

    def test_parity(self):
        for n in range(0, 20000):
            parity(pack.uint, unpack.uint, n, self.assertEqual)


class IntTest(TestCase):

    def test(self):
        cases = [
            ((b'\xbf\xffA',),       (-524257,   3)),
            ((b'\x01\xFF',),        (-1,        1)),
            ((b'\x00\xFF',),        (0,         1)),
            ((b'A',),               (-33,       1)),
            ((b'Alen',),            (-33,       1)),
            ((b'\x88\x00',),        (512,       2)),
            ((b'\x88\x00\x00',),    (512,       2)),
            ((b'\x01',),            (-1,        1)),
            ((b'\xFF\x00',),        (8128,      2)),
            ((b'Alen', 1),          (54,        2)),
            ((b'\x00\x88\x00', 1),  (512,       3)),
            ((b'\x00\x00\x00', 1),  (0,         2))
        ]
        for args, expected in cases:
            self.assertEqual(unpack.int_(*args), expected)

    def test_parity(self):
        for n in range(-20000, 20000):
            parity(pack.int_, unpack.int_, n, self.assertEqual)


class StrTest(TestCase):

    def test_parity(self):
        characters = string.ascii_letters + string.digits + ' '
        for n in range(100):
            length = random.randint(0, 10)
            case = ''.join(random.choice(characters) for _ in range(length))
            parity(pack.str_, unpack.str_, case, self.assertEqual)


class BoolTest(TestCase):

    def test_parity(self):
        parity(pack.bool_, unpack.bool_, True, self.assertEqual)
        parity(pack.bool_, unpack.bool_, False, self.assertEqual)


class NoneTest(TestCase):

    def test_parity(self):
        parity(pack.none, unpack.none, None, self.assertEqual)


class FloatTest(TestCase):

    def test_parity(self):
        def assert_nans(a, b):
            self.assertTrue(isnan(a))
            self.assertTrue(isnan(b))

        def gen(start, stop, steps):
            step = (stop - start) / steps
            return [stop + i * step for i in range(steps)]

        cases = []
        cases.extend(gen(-1e20, 1e20, 2500))
        cases.extend(gen(-1, 1, 2500))
        cases.extend([float('inf'), -float('inf'), 0.0, -0.0])
        for case in cases:
            parity(pack.float_, unpack.float_, case, self.assertEqual)
        parity(pack.float_, unpack.float_, float('nan'), assert_nans)
        parity(pack.float_, unpack.float_, -float('nan'), assert_nans)


class TypeTest(TestCase):

    def test_ordered(self):
        pass

    @patch('starparse.config.ORDERED_DICT', False)
    def test_unordered(self):
        cases = [
            ((b'\x01',),    (None, 1)),
            ((b'\x02',),    (float, 1)),
            ((b'\x03',),    (bool, 1)),
            ((b'\x04',),    (int, 1)),
            ((b'\x05',),    (str, 1)),
            ((b'\x06',),    (list, 1)),
            ((b'\x07',),    (dict, 1)),
        ]
        for args, expected in cases:
            self.assertEqual(unpack.type_(*args), expected)

    @patch('starparse.config.ORDERED_DICT', True)
    def test_unordered(self):
        cases = [
            ((b'\x01',), (None, 1)),
            ((b'\x02',), (float, 1)),
            ((b'\x03',), (bool, 1)),
            ((b'\x04',), (int, 1)),
            ((b'\x05',), (str, 1)),
            ((b'\x06',), (list, 1)),
            ((b'\x07',), (dict, 1)),
        ]
        for args, expected in cases:
            self.assertEqual(unpack.type_(*args), expected)


class ListTest(TestCase):

    # TODO: Mock out other functions
    def test_parity(self):
        cases = [[], [1, 2, 3], ["a", "b", "c"], [1, "b", []]]
        for case in cases:
            parity(pack.list_, unpack.list_, case, self.assertEqual)


class DictTest(TestCase):

    # TODO: Mock out other functions
    @patch('starparse.config.ORDERED_DICT', False)
    def test_parity(self):
        cases = [{}, {"a": 1, "b": 2}, {"a": "a", "b": 2}, {"a": {"b": {}}}]
        for case in cases:
            parity(pack.dict_, unpack.dict_, case, self.assertEqual)

    # TODO: Mock out other functions
    @patch('starparse.config.ORDERED_DICT', True)
    def test_parity(self):
        cases = [
            OrderedDict({}),
            OrderedDict({"a": 1, "b": 2}),
            OrderedDict({"a": "a", "b": 2}),
            OrderedDict({"a": OrderedDict({"b": OrderedDict({})})})
        ]
        for case in cases:
            parity(pack.dict_, unpack.dict_, case, self.assertEqual)
