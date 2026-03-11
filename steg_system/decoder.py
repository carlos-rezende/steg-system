from PIL import Image

from .utils import HEADER_BITS, decode_payload


def _extract_all_r(pixels, width: int, height: int) -> str:
    """Extract all bits from R channel LSB (1 bit per pixel)."""
    bits = ''
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            bits += str(r & 1)
    return bits


def _extract_data_bits(
    pixels,
    width: int,
    height: int,
    channels: int,
    bits_per_channel: int,
    num_bits: int,
) -> str:
    """Extract data bits from pixel HEADER_BITS onwards using the given mode."""
    bits = ''
    pixel_idx = 0

    for y in range(height):
        for x in range(width):
            if len(bits) >= num_bits:
                return bits

            r, g, b, a = pixels[x, y]
            pixel_idx += 1

            if pixel_idx <= HEADER_BITS:
                continue

            for ch in range(channels):
                for bp in range(bits_per_channel):
                    if len(bits) >= num_bits:
                        return bits
                    val = [r, g, b, a][ch]
                    bits += str((val >> bp) & 1)

    return bits


def decode_image(image: str, *, legacy_mode: bool = False) -> bytes:
    """Decode a payload from an image.

    Reads header (first HEADER_BITS bits from R) to detect format and mode,
    then extracts the rest accordingly. Legacy images use R-only 1bpp.

    legacy_mode: Se True, aceita imagens codificadas antes do magic bytes.
    """

    img = Image.open(image)
    if img.format == 'GIF' or image.lower().endswith('.gif'):
        from .gif import decode_gif

        return decode_gif(image, legacy_mode=legacy_mode)

    img = img.convert('RGBA')
    pixels = img.load()

    header_bits = ''
    for y in range(img.height):
        for x in range(img.width):
            if len(header_bits) >= HEADER_BITS:
                break
            r, g, b, a = pixels[x, y]
            header_bits += str(r & 1)
        if len(header_bits) >= HEADER_BITS:
            break

    if len(header_bits) < 33:
        # Not enough for any format - try legacy with full R stream
        all_bits = _extract_all_r(pixels, img.width, img.height)
        return decode_payload('0' + all_bits, legacy_mode=legacy_mode)

    version = header_bits[0]
    if version == '0':
        all_bits = _extract_all_r(pixels, img.width, img.height)
        return decode_payload('0' + all_bits, legacy_mode=legacy_mode)

    if len(header_bits) < HEADER_BITS:
        return b''

    ch_map = {'00': 1, '01': 3, '10': 4}
    channels = ch_map.get(header_bits[2:4], 1)
    bits_per_channel = 2 if header_bits[4] == '1' else 1
    length = int(header_bits[5:37], 2)
    data_bits_needed = length * 8

    data_bits = _extract_data_bits(
        pixels, img.width, img.height, channels, bits_per_channel, data_bits_needed
    )
    bits = header_bits + data_bits
    return decode_payload(bits, legacy_mode=legacy_mode)
