from collections import Counter

from PIL import Image, ImageSequence


def _lsb_distribution(bits: str) -> dict:
    c = Counter(bits)
    total = c['0'] + c['1']
    return {
        'total_bits': total,
        'zeros': c['0'],
        'ones': c['1'],
        'ratio_ones': c['1'] / total if total else 0,
    }


def detect_steganography(image_path: str) -> dict:
    """Return a lightweight heuristic report about possible steganography.

    The method computes the distribution of least-significant bits (LSB) across
    an image (or GIF frames). A distribution very close to 0.5 (with low
    variance) can indicate hidden data; natural images tend to have more skew.
    Uses stricter thresholds to reduce false positives.
    """

    img = Image.open(image_path)

    bits = ''
    if img.format == 'GIF' or image_path.lower().endswith('.gif'):
        for frame in ImageSequence.Iterator(img):
            frame = frame.convert('P')
            pixels = frame.load()
            for y in range(frame.height):
                for x in range(frame.width):
                    bits += str(pixels[x, y] & 1)
    else:
        img = img.convert('RGBA')
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                bits += str(r & 1)

    report = _lsb_distribution(bits)
    ratio = report['ratio_ones']
    total = report['total_bits']

    if total >= 5000 and 0.495 <= ratio <= 0.505:
        report['heuristic'] = "likely-stego"
    else:
        report['heuristic'] = "likely-clean"

    return report
