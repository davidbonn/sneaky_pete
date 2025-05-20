
import unittest

import secrets
from pathlib import Path
import fakefs
import sneaky

fat_tmp = Path("sneaky.fat")
data_tmp = Path("sneaky.data")
result_tmp = Path("sneaky.result")

class TestSneaky(unittest.TestCase):
    def setUp(self):
        fakefs.new_fat_fs_for_linux(str(fat_tmp), '1G')

    def tearDown(self):
        fat_tmp.unlink(missing_ok=True)
        data_tmp.unlink(missing_ok=True)
        result_tmp.unlink(missing_ok=True)

    def test_bleach(self):
        """ this is a good place to do file integrity checks """
        size_before = fat_tmp.stat().st_size
        sneaky.bleach(str(fat_tmp))
        size_after = fat_tmp.stat().st_size

        self.assertEqual(size_before, size_after)

    def put_check_get(self, size=1024):
        data = secrets.token_bytes(size)
        passphrase = secrets.token_urlsafe(32)

        with open(data_tmp, "wb") as f:
            f.write(data)

        sneaky.put(str(fat_tmp), str(data_tmp), passphrase, offset=1)

        rc = sneaky.check(str(fat_tmp), passphrase, offset=1)
        self.assertTrue(rc)

        rc = sneaky.get(str(fat_tmp), str(result_tmp), passphrase, offset=1)
        self.assertTrue(rc)

        with open(result_tmp, "rb") as f:
            result_data = f.read()

        self.assertEqual(data, result_data)


    def test_put_check_get_small(self):
        self.put_check_get(size=1024)
        pass

    def test_put_check_get_large(self):
        self.put_check_get(size=3*1024*1024)

