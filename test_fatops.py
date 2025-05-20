
import unittest

import secrets
import hashlib
from pathlib import Path

from pyfatfs.PyFat import PyFat

import fakefs
import fatops


fat_tmp = Path('fat_test_tmp.fat')

class TestFatops(unittest.TestCase):
    def setUp(self):
        fakefs.new_fat_fs_for_linux(str(fat_tmp), '1G')

    def tearDown(self):
        fat_tmp.unlink(missing_ok=True)

    def test_device_len(self):
        with PyFat.open_fs(str(fat_tmp)) as fs:
            self.assertEqual(fatops.device_len(fs), 1024*1024*1024)

    def test_free_clusters(self):
        with PyFat.open_fs(str(fat_tmp)) as fs:
            result = fatops.free_clusters(fs)
            self.assertTrue(len(result) > 0)

            backwards = fatops.free_clusters(fs, -1)
            self.assertEqual(backwards, result[::-1])

    def test_write_read_slug(self):
        with PyFat.open_fs(str(fat_tmp)) as fs:
            data = secrets.token_bytes(1024*1024)
            clusters = len(data) // fs.bytes_per_cluster

            for pos in [1, -1]:
                free_clusters = fatops.free_clusters(fs, pos)
                fatops.write_slug(fs, free_clusters,data)
                read_slug = fatops.read_slug(fs, clusters, free_clusters)
                self.assertEqual(len(read_slug), len(data))
                self.assertEqual(read_slug, data)
