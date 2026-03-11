"""Testes para o steg-system."""

import tempfile
from pathlib import Path

from PIL import Image

from steg_system.decoder import decode_image
from steg_system.detect import detect_steganography
from steg_system.encoder import encode_image
from steg_system.utils import HEADER_BITS, capacity_bytes, decode_payload, encode_payload


def test_encode_decode_roundtrip():
    """Testa encode e decode de mensagem em PNG."""
    img = Image.new("RGBA", (100, 100), (128, 128, 128, 255))
    img_path = Path(tempfile.mktemp(suffix=".png"))
    img.save(img_path)

    msg = b"Hello, secret!"
    out_path = Path(tempfile.mktemp(suffix=".png"))
    try:
        encode_image(str(img_path), str(out_path), msg)
        result = decode_image(str(out_path))
        assert result == msg
    finally:
        img_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


def test_encode_decode_with_compression():
    """Testa encode/decode com compressão."""
    img = Image.new("RGBA", (200, 200), (100, 100, 100, 255))
    img_path = Path(tempfile.mktemp(suffix=".png"))
    img.save(img_path)

    msg = "A" * 500
    out_path = Path(tempfile.mktemp(suffix=".png"))
    try:
        encode_image(str(img_path), str(out_path), msg.encode("utf-8"), compress=True)
        result = decode_image(str(out_path))
        assert result.decode("utf-8") == msg
    finally:
        img_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


def test_capacity_bytes():
    """Testa cálculo de capacidade."""
    cap = capacity_bytes(100, 100, channels=1, bits_per_channel=1)
    assert cap > 0
    assert cap == (100 * 100 - HEADER_BITS) // 8

    cap3 = capacity_bytes(100, 100, channels=3, bits_per_channel=1)
    assert cap3 > cap
    assert cap3 == (100 * 100 - HEADER_BITS) * 3 // 8


def test_encode_payload_decode_payload():
    """Testa encode_payload e decode_payload."""
    data = b"test"
    bits = encode_payload(data, compress=False)
    decoded = decode_payload(bits)
    assert decoded == data


def test_decode_legacy_mode():
    """Modo legado aceita payload com ou sem magic."""
    bits = encode_payload(b"legacy", compress=False)
    decoded = decode_payload(bits, legacy_mode=True)
    assert decoded == b"legacy"


def test_detect_steganography():
    """Testa detecção heurística."""
    img = Image.new("RGBA", (50, 50), (128, 128, 128, 255))
    path = Path(tempfile.mktemp(suffix=".png"))
    img.save(path)
    try:
        report = detect_steganography(str(path))
        assert "heuristic" in report
        assert report["heuristic"] in ("likely-stego", "likely-clean")
        assert "total_bits" in report
    finally:
        path.unlink(missing_ok=True)
