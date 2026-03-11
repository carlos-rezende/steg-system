import argparse
import sys
from base64 import b64decode, b64encode

from .crypto import decrypt, encrypt
from .decoder import decode_image
from .detect import detect_steganography
from .encoder import encode_image


def _encode(args: argparse.Namespace) -> int:
    payload: bytes

    if args.payload_file:
        with open(args.payload_file, 'rb') as f:
            payload = f.read()
    elif args.message_file:
        with open(args.message_file, 'r', encoding='utf-8') as f:
            payload = f.read().encode('utf-8')
    elif args.message is not None:
        payload = args.message.encode('utf-8')
    else:
        raise SystemExit(
            "Either --message or --message-file or --payload-file must be provided")

    if args.password:
        payload = encrypt(payload, args.password)

    encode_image(
        args.input,
        args.output,
        payload,
        compress=not args.no_compress,
        channels=args.channels,
        bits_per_channel=args.bits,
    )
    return 0


def _decode(args: argparse.Namespace) -> int:
    payload = decode_image(args.input, legacy_mode=args.legacy)

    if args.password:
        try:
            payload = decrypt(payload, args.password)
        except Exception as ex:
            print(f"Failed to decrypt payload: {ex}", file=sys.stderr)
            return 2

    if args.output:
        with open(args.output, 'wb') as f:
            f.write(payload)
    else:
        try:
            print(payload.decode('utf-8'))
        except UnicodeDecodeError:
            if args.raw:
                print(b64encode(payload).decode('ascii'))
            else:
                print("<binary payload: use --raw to print base64>")

    return 0


def _detect(args: argparse.Namespace) -> int:
    report = detect_steganography(args.input)
    for key, value in report.items():
        print(f"{key}: {value}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="steg_system")
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser(
        "encode", help="Embed a message or file into an image")
    enc.add_argument("--input", "-i", required=True, help="Input image path")
    enc.add_argument("--output", "-o", required=True, help="Output image path")
    enc.add_argument("--message", "-m", help="Message to embed (UTF-8)")
    enc.add_argument("--message-file", help="Text file containing the message")
    enc.add_argument("--payload-file", help="Binary file to embed (any bytes)")
    enc.add_argument("--password", "-p",
                     help="Optional passphrase to encrypt the payload")
    enc.add_argument("--no-compress", action="store_true",
                     help="Disable zlib compression (for already-compressed files)")
    enc.add_argument("--channels", type=int, choices=[1, 3, 4], default=1,
                     help="Channels to use: 1=R, 3=RGB, 4=RGBA (default: 1)")
    enc.add_argument("--bits", type=int, choices=[1, 2], default=1,
                     help="Bits per channel: 1 or 2 (default: 1)")
    enc.set_defaults(func=_encode)

    dec = sub.add_parser("decode", help="Extract a payload from an image")
    dec.add_argument("--input", "-i", required=True, help="Input image path")
    dec.add_argument("--output", "-o",
                     help="Write payload to a file instead of stdout")
    dec.add_argument("--password", "-p",
                     help="Passphrase used to decrypt the payload")
    dec.add_argument("--legacy", action="store_true",
                     help="Decode images encoded before magic bytes (risk of false positives)")
    dec.add_argument("--raw", action="store_true",
                     help="Print raw bytes as base64 if not UTF-8")
    dec.set_defaults(func=_decode)

    det = sub.add_parser(
        "detect", help="Detect likely steganography in an image")
    det.add_argument("--input", "-i", required=True, help="Input image path")
    det.set_defaults(func=_detect)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
