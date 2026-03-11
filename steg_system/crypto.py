from typing import Optional, Tuple, Union

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

KEY = b'minhachavesecreta'
SALT_SIZE = 16
PBKDF2_ROUNDS = 200_000


def _derive_key(passphrase: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """Derive an AES key from a passphrase and salt.

    Returns a tuple of (key, salt).
    """

    if salt is None:
        salt = get_random_bytes(SALT_SIZE)

    key = PBKDF2(passphrase, salt, dkLen=32,
                 count=PBKDF2_ROUNDS, hmac_hash_module=SHA256)
    return key, salt


def encrypt(data: Union[str, bytes], passphrase: Optional[str] = None) -> bytes:
    """Encrypt bytes (or UTF-8 string) and return raw bytes.

    When a `passphrase` is given, the output is:
        salt(16) || iv(16) || ciphertext

    Otherwise the output is:
        iv(16) || ciphertext
    """

    if isinstance(data, str):
        data_bytes = data.encode('utf-8')
    else:
        data_bytes = data

    if passphrase:
        key, salt = _derive_key(passphrase)
    else:
        key = KEY
        salt = b''

    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data_bytes, AES.block_size))
    return salt + cipher.iv + ct_bytes


def decrypt(data: bytes, passphrase: Optional[str] = None) -> bytes:
    """Decrypt data produced by :func:`encrypt`.

    When a passphrase is present, the function expects the first 16 bytes to be the salt.
    """

    if passphrase:
        salt = data[:SALT_SIZE]
        iv = data[SALT_SIZE: SALT_SIZE + 16]
        ct = data[SALT_SIZE + 16:]
        key, _ = _derive_key(passphrase, salt)
    else:
        iv = data[:16]
        ct = data[16:]
        key = KEY

    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)
