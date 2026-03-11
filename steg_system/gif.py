from PIL import Image, ImageSequence

from .utils import decode_payload, encode_payload


def encode_gif(input_gif: str, output_gif: str, payload: bytes):
    """Embed a payload across the frames of an animated GIF."""

    img = Image.open(input_gif)
    frames = [frame.copy().convert('P')
              for frame in ImageSequence.Iterator(img)]

    bits = encode_payload(payload)
    capacity = sum(f.width * f.height for f in frames)
    if len(bits) > capacity:
        raise ValueError(
            f"Payload too long for GIF capacity ({len(bits)} bits vs {capacity} pixels)"
        )

    bit_index = 0
    for frame in frames:
        pixels = frame.load()
        for y in range(frame.height):
            for x in range(frame.width):
                if bit_index >= len(bits):
                    break

                val = pixels[x, y]
                pixels[x, y] = (val & ~1) | int(bits[bit_index])
                bit_index += 1
            if bit_index >= len(bits):
                break

    save_kwargs = {
        'save_all': True,
        'append_images': frames[1:],
        'loop': img.info.get('loop', 0),
        'duration': img.info.get('duration', 100),
    }
    if 'disposal' in img.info:
        save_kwargs['disposal'] = img.info['disposal']

    frames[0].save(output_gif, **save_kwargs)


def decode_gif(input_gif: str, *, legacy_mode: bool = False) -> bytes:
    """Extract a hidden payload from an animated GIF."""

    img = Image.open(input_gif)

    bits = ''
    for frame in ImageSequence.Iterator(img):
        frame = frame.convert('P')
        pixels = frame.load()
        for y in range(frame.height):
            for x in range(frame.width):
                bits += str(pixels[x, y] & 1)

    return decode_payload(bits, legacy_mode=legacy_mode)
