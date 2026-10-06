"""Tests for the compact binary sync protocol."""
import unittest

from companion.wire import (
    MESSAGE_SIZE,
    MessageType,
    SyncMessage,
    compute_base_version_hash,
    decode_message,
    encode_message,
)


class TestWireProtocol(unittest.TestCase):
    def test_round_trips_every_message_type(self):
        for message_type in MessageType:
            with self.subTest(message_type=message_type):
                message = SyncMessage(
                    message_type=message_type,
                    base_version_hash=0x12345678,
                    entity_id=0x90ABCDEF,
                    timestamp=1_700_000_000,
                    sender_id=0xBEEF,
                )
                packet = encode_message(message)
                self.assertEqual(len(packet), MESSAGE_SIZE)
                self.assertEqual(decode_message(packet), message)

    def test_fixed_width_fields_use_network_byte_order(self):
        packet = encode_message(SyncMessage(
            MessageType.PIN_ADD, 0x01020304, 0x05060708, 0x090A0B0C, 0x0D0E
        ))
        self.assertEqual(packet, bytes.fromhex("01 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e"))

    def test_missing_timestamp_is_encoded_as_zero_and_decoded_as_none(self):
        packet = encode_message(SyncMessage(MessageType.PIN_REMOVE, 1, 2, None, 3))
        self.assertEqual(packet[9:13], b"\0\0\0\0")
        self.assertEqual(MESSAGE_SIZE, 15)
        self.assertIsNone(decode_message(packet).timestamp)

    def test_hash_is_first_four_sha256_bytes_as_big_endian_u32(self):
        self.assertEqual(compute_base_version_hash(b"base-v1"), 0x6A9AC230)
        self.assertEqual(compute_base_version_hash("base-v1"), 0x6A9AC230)

    def test_rejects_invalid_packet_length_and_message_type(self):
        with self.assertRaises(ValueError):
            decode_message(b"\x01")
        packet = bytearray(MESSAGE_SIZE)
        packet[0] = 255
        with self.assertRaises(ValueError):
            decode_message(packet)

    def test_rejects_values_outside_field_widths(self):
        with self.assertRaises(ValueError):
            encode_message(SyncMessage(MessageType.PIN_ADD, 1 << 32, 1, None, 1))
        with self.assertRaises(ValueError):
            encode_message(SyncMessage(MessageType.PIN_ADD, 1, 1 << 32, None, 1))
        with self.assertRaises(ValueError):
            encode_message(SyncMessage(MessageType.PIN_ADD, 1, 1, -1, 1))
        with self.assertRaises(ValueError):
            encode_message(SyncMessage(MessageType.PIN_ADD, 1, 1, None, 1 << 16))


if __name__ == "__main__":
    unittest.main()
