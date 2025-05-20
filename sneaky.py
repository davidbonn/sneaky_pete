#!/usr/bin/env python3

import argparse
import hashlib
import secrets
from pathlib import Path
from getpass import getpass
import sys

from pyfatfs.PyFat import PyFat
from progressbar import ProgressBar, GranularBar, Percentage

import fatops
import slug

widgets = [GranularBar(),' ', Percentage()]


def get_key_from_passphrase(passphrase):
    if len(passphrase) == 0:
        passphrase = getpass("Passphrase: ")

    h = hashlib.sha256()
    h.update(passphrase.encode("utf-8"))
    return h.digest()


def info(block_device, verbose=False):
    print(f"info: block_device={block_device}")

    with PyFat.open_fs(block_device) as fs:
        print(f"info: {fs.fat_type=}")
        print(f"info: {fs.bytes_per_cluster=}")
        print(f"info: {len(fs.fat)=}")
        print(f"info: {fs.fat[-1]=}")

        free_clusters = fatops.free_clusters(fs)
        print(f"info: {len(free_clusters)=}")


def check(block_device, passphrase, offset, verbose=False):
    my_key = get_key_from_passphrase(passphrase)

    with PyFat.open_fs(block_device) as fs:
        free_clusters, my_slug = read_full_slug(fs, my_key, offset, verbose)
        if not slug.check_full_slug(my_slug):
            print("Error: invalid slug but okay header")
            return False

        return True


def bleach(block_device, verbose=False):
    with PyFat.open_fs(block_device) as fs:
        free_clusters = fatops.free_clusters(fs)

        if not verbose:
            for i, cluster in enumerate(free_clusters):
                fatops.write_cluster(fs, cluster, secrets.token_bytes(fs.bytes_per_cluster))
        else:
            with ProgressBar(widgets=widgets, maxval=len(free_clusters)) as pbar:
                for i, cluster in enumerate(free_clusters):
                    pbar.update(i)
                    fatops.write_cluster(fs, cluster, secrets.token_bytes(fs.bytes_per_cluster))


def get(block_device, target, passphrase, offset, verbose=False):
    my_key = get_key_from_passphrase(passphrase)

    with PyFat.open_fs(block_device) as fs:
        free_clusters, full_slug = read_full_slug(fs, my_key, offset, verbose)

        if not slug.extract_slug(full_slug, target):
            print("Error: invalid slug but acceptable header")
            return False

    return True


def put(block_device, target, passphrase, offset, verbose=False):
    my_key = get_key_from_passphrase(passphrase)

    with PyFat.open_fs(block_device) as fs:
        free_clusters = fatops.free_clusters(fs, offset)
        my_slug = slug.make_slug(target, fs.bytes_per_cluster)
        my_slug = slug.encrypt_slug(my_slug, my_key)
        fatops.write_slug(fs, free_clusters, my_slug)


def read_full_slug(fs, my_key, offset=1, verbose=False):
    free_clusters = fatops.free_clusters(fs, offset)
    first_slug = fatops.read_slug(fs, 1, free_clusters)
    if first_slug is None:
        print("Error: no slug found")
        exit(1)

    clean_slug = slug.decrypt_slug(first_slug, my_key)
    header = slug.check_slug_header(clean_slug)

    if verbose:
        print(f"info: {header['clusters']} clusters")
        print(f"info: {header['length']} bytes")

    if header is None:
        print("Error: invalid slug")
        exit(1)

    clusters = int(header["clusters"])

    if clusters > 1:
        my_slug = fatops.read_slug(fs, int(header["clusters"]), free_clusters)
    else:
        my_slug = first_slug

    return free_clusters, slug.decrypt_slug(my_slug, my_key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", type=str, default=None, required=True)
    ap.add_argument("--passphrase", type=str, default=None, required=False)
    ap.add_argument("--verbose", action="store_true", default=False)
    ap.add_argument("--info", action="store_true", default=False)
    ap.add_argument("--check", action="store_true", default=False)
    ap.add_argument("--bleach", action="store_true", default=False)
    ap.add_argument("--offset", type=int, default=1)
    ap.add_argument("--get", type=str, default=None)
    ap.add_argument("--put", type=str, default=None)
    args = ap.parse_args()

    block_device = Path(args.block)
    if not block_device.exists():
        print(f"Error: block device {block_device} does not exist")
        exit(1)

    if args.get is not None and args.put is not None:
        print("Error: cannot use --get and --put together")
        exit(1)

    if args.check is not None and args.get is not None and args.put is not None:
        if args.passphrase is None:
            print("Error: --passphrase is required when using --check, --get or --put")
            exit(1)

    if args.info:
        info(block_device, args.verbose)

    if args.check:
        check(block_device, args.passphrase, args.offset, args.verbose)

    if args.get is not None:
        get(block_device, args.get, args.passphrase, args.offset, args.verbose)
    elif args.put is not None:
        put(block_device, args.put, args.passphrase, args.offset, args.verbose)

    if args.bleach:
        bleach(block_device, args.verbose)


if __name__ == "__main__":
    main()
