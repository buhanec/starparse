from unittest import TestCase
from unittest.mock import patch
from starparse import pack, unpack
import os


class CITest(TestCase):

    def setUp(self):
        TEST_DIR = 'starparse/tests/ci_players'
        self.players = {}
        for file in next(os.walk(TEST_DIR))[2]:
            if file.endswith('.player'):
                with open(os.path.join(TEST_DIR, file), 'rb') as f:
                    self.players[file] = f.read()

    @patch('starparse.config.ORDERED_DICT', False)
    def test_unordered(self):
        for file, player in self.players.items():
            # Unpack
            save_format, entity, flags, offset = unpack.header(player, 0)
            unpacked, limit = unpack.typed(player, offset)
            self.assertEqual(limit, len(player))
            self.assertEqual(save_format, b'SBVJ01')

            # Pack
            packed = (pack.header(save_format, entity, flags) +
                      pack.typed(unpacked))
            self.assertEqual(len(packed), len(player))

            # Re-unpack
            sf_2, entity_2, flags_2, offset_2 = unpack.header(packed, 0)
            unpacked_2, limit_2 = unpack.typed(packed, offset_2)
            self.assertEqual(save_format, sf_2)
            self.assertEqual(entity, entity_2)
            self.assertEqual(flags, flags_2)
            self.assertEqual(offset, offset_2)
            self.assertEqual(limit, limit_2)
            self.assertEqual(unpacked, unpacked_2)

    @patch('starparse.config.ORDERED_DICT', True)
    def test_ordered(self):
        for file, player in self.players.items():
            # Unpack
            save_format, entity, flags, offset = unpack.header(player, 0)
            unpacked, limit = unpack.typed(player, offset)
            self.assertEqual(limit, len(player))
            self.assertEqual(save_format, b'SBVJ01')

            # Pack
            packed = (pack.header(save_format, entity, flags) +
                      pack.typed(unpacked))
            self.assertEqual(len(packed), len(player))

            # Re-unpack
            save_format_2, entity_2, flags_2, offset_2 = unpack.header(packed,
                                                                       0)
            unpacked_2, limit_2 = unpack.typed(packed, offset_2)
            self.assertEqual(save_format, save_format_2)
            self.assertEqual(entity, entity_2)
            self.assertEqual(flags, flags_2)
            self.assertEqual(offset, offset_2)
            self.assertEqual(limit, limit_2)
            self.assertEqual(unpacked, unpacked_2)

            self.assertEqual(packed, player)
