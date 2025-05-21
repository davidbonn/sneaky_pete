"""
    make a fake FAT filesystem and put stuff on it
    for testing
"""

import hashlib
import io
import secrets
import subprocess

from pyfatfs.PyFat import PyFat


def parse_size(size: str):
    """ returns size in kbytes (bytes / 1024) from a string like "16M"""
    actual_size = int(size[:-1])
    code = size[-1]

    if code == "M":
        scale = 1
    elif code == "G":
        scale = 1024
    else:
        raise ValueError("Invalid size code")

    actual_size *= scale
    actual_size *= 1024

    return actual_size


def new_fat_fs(filename: str, size: str):
    """
        :param filename: file name
        :param size: as a str line "32M" or "16G"

        might want to use mkfs.fat on Linux if we can
    """
    actual_size = parse_size(size)

    megabyte = b'\x00' * 1024 * 1024

    with open(filename, "wb") as f:
        for i in range(actual_size // 1024):
            f.write(megabyte)

    fs = PyFat()

    with open(filename, "rb+") as f:
        fs.__fp = f
        fs.mkfs(filename, PyFat.FAT_TYPE_FAT32, actual_size)


def new_fat_fs_for_linux(filename: str, size: str):
    actual_size = parse_size(size)
    subprocess.run(["mkfs.fat", "-C", filename, str(actual_size)])


def add_file(fs, filename: str, size: int):
    fio, digest = fake_file(size)
    with fs.open(filename, "wb") as f:
        f.write(fio.getvalue())
    return filename, digest


def get_file_hash(fs, filename: str):
    io_obj = io.BytesIO()
    with fs.open(filename, "rb") as f:
        io_obj.write(f.read())
    return hashlib.sha256(io_obj.getvalue()).hexdigest()


def fake_file(size: int):
    """ returns an in-memory bytes IO object with random data and a hash of the data in it """
    my_bytes = secrets.token_bytes(size)
    h = hashlib.sha256()
    h.update(my_bytes)
    rc = h.hexdigest()
    return io.BytesIO(my_bytes), rc
