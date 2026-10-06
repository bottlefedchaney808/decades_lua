"""Compact fixed-width binary protocol for Decades sync events.

Packets use network byte order and are exactly 15 bytes:

    type:u8 | base_version_hash:u32 | entity_id:u32 | timestamp:u32 | sender_id:u16

The listed field widths sum to 15 bytes. The supplied byte ranges are each
shifted one byte early after the type and cannot fit a u32 hash; this module
uses the coherent layout implied by the field widths: hash at bytes 1-4, entity
ID at 5-8, timestamp at 9-12, sender ID at 13-14. A zero timestamp means
that no timestamp was supplied. No JSON or protobuf envelope is used on wire.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from enum import IntEnum

__all__ = [
    "MESSAGE_SIZE",
    "MessageType",
    "SyncMessage",
    "compute_base_version_hash",
    "decode_message",
    "encode_message",
]

_PACKET = struct.Struct(">BIIIH")
MESSAGE_SIZE = _PACKET.size


class MessageType(IntEnum):
    PIN_ADD = 1
    PIN_REMOVE = 2
    NODE_DEPLETION = 3
    GROUP_TARGET = 4


@dataclass(frozen=True)
class SyncMessage:
    """A sync event; timestamp is None when absent."""

    message_type: MessageType
    base_version_hash: int
    entity_id: int
    timestamp: int | None
    sender_id: int


def compute_base_version_hash(base_version: str | bytes) -> int:
    """Return the first four SHA-256 digest bytes as an unsigned big-endian int."""
    if isinstance(base_version, str):
        base_version = base_version.encode("utf-8")
    if not isinstance(base_version, bytes):
        raise TypeError("base_version must be str or bytes")
    return int.from_bytes(hashlib.sha256(base_version).digest()[:4], "big")


def _uint(name: str, value: int, bits: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not 0 <= value < (1 << bits):
        raise ValueError(f"{name} must fit in u{bits}")
    return value


def encode_message(message: SyncMessage) -> bytes:
    """Encode one sync event into its compact, exactly 15-byte packet."""
    try:
        message_type = MessageType(message.message_type)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"unknown message type: {message.message_type!r}") from exc
    base_hash = _uint("base_version_hash", message.base_version_hash, 32)
    entity_id = _uint("entity_id", message.entity_id, 32)
    timestamp = 0 if message.timestamp is None else _uint("timestamp", message.timestamp, 32)
    sender_id = _uint("sender_id", message.sender_id, 16)
    return _PACKET.pack(message_type, base_hash, entity_id, timestamp, sender_id)


def decode_message(packet: bytes | bytearray | memoryview) -> SyncMessage:
    """Decode one exact-size packet; zero timestamp is returned as None."""
    try:
        view = memoryview(packet)
    except TypeError as exc:
        raise ValueError("packet must be bytes-like") from exc
    if view.nbytes != MESSAGE_SIZE:
        raise ValueError(f"packet must be exactly {MESSAGE_SIZE} bytes")
    try:
        raw_type, base_hash, entity_id, timestamp, sender_id = _PACKET.unpack(view)
    except struct.error as exc:
        raise ValueError("invalid packet") from exc
    try:
        message_type = MessageType(raw_type)
    except ValueError as exc:
        raise ValueError(f"unknown message type: {raw_type}") from exc
    return SyncMessage(
        message_type=message_type,
        base_version_hash=base_hash,
        entity_id=entity_id,
        timestamp=timestamp or None,
        sender_id=sender_id,
    )
