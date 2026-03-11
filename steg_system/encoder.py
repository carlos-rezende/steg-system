from PIL import Image

from .utils import (
    HEADER_BITS,
    bits_per_pixel,
    encode_payload,
)


def _embed_bits_simple(
    pixels,
    width: int,
    height: int,
    bits: str,
    channels: int,
    bits_per_channel: int,
) -> None:
    """Embed bits: first HEADER_BITS from R, then data in row-major with mode."""
    data_index = 0

    for y in range(height):
        for x in range(width):
            if data_index >= len(bits):
                return

            r, g, b, a = pixels[x, y]
            pixel_idx = y * width + x

            if pixel_idx < HEADER_BITS:
                r = (r & ~1) | int(bits[data_index])
                data_index += 1
            else:
                for ch in range(channels):
                    for bp in range(bits_per_channel):
                        if data_index >= len(bits):
                            break
                        val = [r, g, b, a][ch]
                        bit_val = int(bits[data_index])
                        val = (val & ~(1 << bp)) | (bit_val << bp)
                        if ch == 0:
                            r = val
                        elif ch == 1:
                            g = val
                        elif ch == 2:
                            b = val
                        else:
                            a = val
                        data_index += 1

            pixels[x, y] = (r, g, b, a)


def encode_image(
    input_img: str,
    output_img: str,
    payload: bytes,
    *,
    compress: bool = True,
    channels: int = 1,
    bits_per_channel: int = 1,
):
    """Encode a payload into an image.

    The payload can be any bytes. Header stores length, compression flag, and mode.
    For animated GIFs it embeds across frames using the pixel-index LSB.
    For WebP stickers it enforces lossless output.

    Args:
        compress: Use zlib compression (default True).
        channels: 1=R only, 3=RGB, 4=RGBA.
        bits_per_channel: 1 or 2 bits per channel.
    """

    img = Image.open(input_img)
    if img.format == 'GIF' or input_img.lower().endswith('.gif') or output_img.lower().endswith('.gif'):
        from .gif import encode_gif

        encode_gif(input_img, output_img, payload)
        return output_img

    img = img.convert('RGBA')
    pixels = img.load()

    bits = encode_payload(
        payload,
        compress=compress,
        channels=channels,
        bits_per_channel=bits_per_channel,
    )

    bpp = bits_per_pixel(channels, bits_per_channel)
    header_capacity = HEADER_BITS
    data_capacity = (img.width * img.height - HEADER_BITS) * bpp
    total_capacity = header_capacity + data_capacity

    if len(bits) > total_capacity:
        raise ValueError(
            f"Payload too long for image capacity ({len(bits)} bits vs {total_capacity} bits, "
            f"mode={channels}ch/{bits_per_channel}bpp)"
        )

    _embed_bits_simple(pixels, img.width, img.height, bits, channels, bits_per_channel)

    save_kwargs = {}
    if output_img.lower().endswith('.webp'):
        save_kwargs['lossless'] = True

    out_path = output_img
    if output_img.lower().endswith(('.jpg', '.jpeg')):
        out_path = output_img.rsplit('.', 1)[0] + '.png'

    img.save(out_path, **save_kwargs)
    return out_path
