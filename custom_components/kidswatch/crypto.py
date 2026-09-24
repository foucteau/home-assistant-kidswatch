from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import quote_plus

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class KidsWatchCrypto:
    """Implement the protocol transformations used by the KidsWatch app."""

    @staticmethod
    def md5(value: str) -> str:
        return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest()

    @classmethod
    def make_seed(cls) -> str:
        raw = secrets.token_bytes(16).hex().upper()
        return cls.md5(raw)

    @staticmethod
    def _java_string_hash(value: str) -> int:
        h = 0
        for ch in value:
            h = (31 * h + ord(ch)) & 0xFFFFFFFF
        return h - 0x100000000 if h & 0x80000000 else h

    @classmethod
    def _java_hashmap_spread(cls, key: str) -> int:
        h = cls._java_string_hash(key) & 0xFFFFFFFF
        return (h ^ (h >> 16)) & 0xFFFFFFFF

    @staticmethod
    def _java_hashmap_capacity(size: int) -> int:
        capacity = 16
        while size > int(capacity * 0.75):
            capacity <<= 1
        return capacity

    @classmethod
    def _java_hashmap_items(cls, parameters: dict[str, str]) -> list[tuple[str, str]]:
        capacity = cls._java_hashmap_capacity(len(parameters))
        buckets: dict[int, list[tuple[str, str]]] = {}
        for key, value in parameters.items():
            index = cls._java_hashmap_spread(key) & (capacity - 1)
            buckets.setdefault(index, []).append((key, value))
        result: list[tuple[str, str]] = []
        for index in range(capacity):
            result.extend(buckets.get(index, ()))
        return result

    @classmethod
    def encode_parameters(cls, parameters: dict[str, str]) -> str:
        parts: list[str] = []
        for key, value in cls._java_hashmap_items(parameters):
            encoded_key = quote_plus(str(key), encoding="utf-8", errors="strict")
            encoded_value = quote_plus(str(value), encoding="utf-8", errors="strict")
            parts.append(f"{encoded_key}={encoded_value}")
        return "&".join(parts)

    @staticmethod
    def _sorted_concat(values: list[str]) -> str:
        return "".join(sorted(values))

    @classmethod
    def make_aes_key(
        cls, *, m2: str, seed: str, timestamp: str,
        token: str = "", secret: str = "", qid: str = "",
    ) -> bytes:
        if token:
            values = [seed, token, secret, cls.md5(qid), cls.md5(timestamp)]
        else:
            m2_part = cls.md5(m2)[9:25]
            values = [seed, cls.md5(m2_part), cls.md5(timestamp)]
        return cls.md5(cls._sorted_concat(values)).encode("ascii")

    @classmethod
    def make_aes_iv(
        cls, *, m2: str, seed: str, timestamp: str,
        token: str = "", secret: str = "", qid: str = "",
    ) -> bytes:
        if token:
            values = [cls.md5(seed), cls.md5(secret), cls.md5(qid), cls.md5(timestamp)]
        else:
            m2_part = cls.md5(m2)[16:25]
            values = [cls.md5(seed), cls.md5(m2_part), cls.md5(timestamp)]
        return cls.md5(cls._sorted_concat(values))[9:25].encode("ascii")

    @staticmethod
    def aes_encrypt(plaintext: str, key: bytes, iv: bytes) -> bytes:
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
        encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        return encryptor.update(padded) + encryptor.finalize()

    @staticmethod
    def aes_decrypt(encrypted: bytes, key: bytes, iv: bytes) -> bytes:
        decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

    @classmethod
    def make_p(
        cls, *, parameters: dict[str, str], m2: str, seed: str, timestamp: str,
        token: str = "", secret: str = "", qid: str = "",
    ) -> str:
        plaintext = cls.encode_parameters(parameters)
        key = cls.make_aes_key(
            m2=m2, seed=seed, timestamp=timestamp, token=token, secret=secret, qid=qid
        )
        iv = cls.make_aes_iv(
            m2=m2, seed=seed, timestamp=timestamp, token=token, secret=secret, qid=qid
        )
        return base64.b64encode(cls.aes_encrypt(plaintext, key, iv)).decode("ascii")
