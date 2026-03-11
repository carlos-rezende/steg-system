"""Utility helpers for the steg-system package."""

import zlib


def bytes_to_bits(data: bytes) -> str:
    """Convert bytes to a bit string."""

    return ''.join(format(b, '08b') for b in data)


def bits_to_bytes(bits: str) -> bytes:
    """Convert a bit string back into raw bytes."""
    bits = bits[: len(bits) - (len(bits) % 8)]
    chunks = [bits[i: i + 8] for i in range(0, len(bits), 8)]
    return bytes(int(c, 2) for c in chunks)


HEADER_BITS = 37
MAGIC = b"STEG"


def encode_payload(
    payload: bytes,
    *,
    compress: bool = True,
    channels: int = 1,
    bits_per_channel: int = 1,
) -> str:
    """Encode a payload with header, optional zlib compression, and mode.

    Format (version 1): [1 version][1 compress][2 ch][1 bpp][32 length][data]
    channels: 1=R, 3=RGB, 4=RGBA. bpp: 1 or 2 bits per channel.
    Legacy (version 0): [0][32 length][data]
    """

    payload = MAGIC + payload

    if compress:
        try:
            payload = zlib.compress(payload, level=9)
        except Exception:
            compress = False

    length = len(payload)
    length_bits = format(length, '032b')
    version = '1'
    compress_bit = '1' if compress else '0'
    ch_bits = {1: '00', 3: '01', 4: '10'}.get(channels, '00')
    bpp_bit = '1' if bits_per_channel == 2 else '0'
    header = version + compress_bit + ch_bits + bpp_bit + length_bits
    return header + bytes_to_bits(payload)


def decode_payload(bits: str, *, legacy_mode: bool = False) -> bytes:
    """Decode a payload from a bit string.

    Supports legacy (version 0) and new format (version 1).
    Legacy: [0][32 length][data]
    New: [1][1 compress][2 ch][1 bpp][32 length][data]

    legacy_mode: Se True, aceita payloads sem magic (imagens antigas). Risco de falsos positivos.
    """

    if len(bits) < 33:
        return b''

    version = bits[0]
    if version == '0':
        # Legacy (sem magic): [0][32 bits length][data]
        length = int(bits[1:33], 2)
        required = 33 + length * 8
        if len(bits) < required:
            return b''
        data_bits = bits[33:required]
        return bits_to_bytes(data_bits)

    if len(bits) < HEADER_BITS:
        return b''

    compress = bits[1] == '1'
    ch_map = {'00': 1, '01': 3, '10': 4}
    channels = ch_map.get(bits[2:4], 1)
    bits_per_channel = 2 if bits[4] == '1' else 1
    length = int(bits[5:37], 2)
    required = HEADER_BITS + length * 8
    if len(bits) < required:
        return b''
    data_bits = bits[HEADER_BITS:required]
    payload = bits_to_bytes(data_bits)

    if compress:
        try:
            payload = zlib.decompress(payload)
        except zlib.error:
            return b''

    if payload.startswith(MAGIC):
        return payload[len(MAGIC):]
    if legacy_mode:
        return payload
    return b''


def bits_per_pixel(channels: int, bits_per_channel: int) -> int:
    """Return number of bits embedded per pixel for the given mode."""
    return channels * bits_per_channel


def capacity_bytes(width: int, height: int, channels: int = 1, bits_per_channel: int = 1) -> int:
    """Return max bytes that fit in an image (PNG/WebP) for the given mode."""
    bpp = bits_per_pixel(channels, bits_per_channel)
    data_bits = max(0, width * height - HEADER_BITS) * bpp
    return data_bits // 8
