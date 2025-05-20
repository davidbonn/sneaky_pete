"""
    build or extract a slug of data
    a "slug" is 17 random bytes, or JSON header padded out, and any file
    it is padded out to take up a whole cluster, usually 32768 bytes
"""

import json
import secrets
import hashlib

from pathlib import Path

from Crypto.Cipher import AES


RANDOM_SLUG_BYTES=17
SLUG_HEADER_BYTES=1024


def blank_slug_header():
    """ make sure that all keys you add are alphabetically between argle and zargle"""
    return {
        "argle": secrets.token_urlsafe(64),
        "clusters": 0,
        "length": 0,
        "sha256hash": "",
        "zargle": secrets.token_urlsafe(64),
        "zzpadding": "",
    }


def slug_header_bytes(slug_header):
    cur_len = len(json.dumps(slug_header, sort_keys=True))
    padding_size = SLUG_HEADER_BYTES - (cur_len + RANDOM_SLUG_BYTES)
    padding = secrets.token_urlsafe(padding_size)
    if len(padding) > padding_size:
        padding = padding[:padding_size]

    slug_header["zzpadding"] = padding

    rc = secrets.token_bytes(RANDOM_SLUG_BYTES) + json.dumps(slug_header, sort_keys=True).encode("ascii")

    return rc


def extract_slug_header(slug_bytes):
    stuff = slug_bytes[RANDOM_SLUG_BYTES:SLUG_HEADER_BYTES]
    return json.loads(stuff.decode("ascii"))


def hardcoded_iv():
    return b"\x00" * 16


def make_slug(src, cluster_size=32768):
    src = Path(src)
    if not src.exists():
        return None

    with open(src, "rb") as f:
        data = f.read()

    header = blank_slug_header()
    clusters = (SLUG_HEADER_BYTES + len(data)) // cluster_size
    if (SLUG_HEADER_BYTES + len(data)) % cluster_size != 0:
        clusters += 1

    header["clusters"] = clusters
    header["length"] = len(data)
    header["sha256hash"] = checksum_data(data)

    return pad_slug(slug_header_bytes(header) + data, cluster_size=cluster_size)


def check_slug_header(first_cluster_bytes):
    try:
        header = extract_slug_header(first_cluster_bytes)
        return header
    except json.decoder.JSONDecodeError:
        return None


def extract_slug(slug_bytes, target, cluster_size=32768):
    header = extract_slug_header(slug_bytes)

    if header is None:
        return False

    data_bytes = slug_bytes[SLUG_HEADER_BYTES:SLUG_HEADER_BYTES + header["length"]]
    with open(target, "wb") as f:
        f.write(data_bytes)

    return True


def check_full_slug(slug_bytes, cluster_size=32768):
    header = extract_slug_header(slug_bytes)

    if header is None:
        return False

    data_bytes = slug_bytes[SLUG_HEADER_BYTES:SLUG_HEADER_BYTES + header["length"]]
    if header["sha256hash"] != checksum_data(data_bytes):
        return False

    return True


def checksum_data(data):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def pad_slug(slug_bytes, cluster_size=32768):
    excess = len(slug_bytes) % cluster_size

    if excess == 0:
        return slug_bytes
    else:
        return slug_bytes + secrets.token_bytes(cluster_size - excess)


def encrypt_slug(slug_bytes, key_bytes, cluster_size=32768):
    cryptor = AES.new(key_bytes, AES.MODE_CBC, hardcoded_iv())
    return cryptor.encrypt(slug_bytes)


def decrypt_slug(slug_bytes, key_bytes, cluster_size=32768):
    cryptor = AES.new(key_bytes, AES.MODE_CBC, hardcoded_iv())
    return cryptor.decrypt(slug_bytes)

