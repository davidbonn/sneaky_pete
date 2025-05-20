
import unittest

import secrets
from pathlib import Path

import slug

temp_slug_file = Path('slug_test.tmp')
temp_extract_file = Path('slug_test_extract.tmp')

class TestSlug(unittest.TestCase):
    def test_blank_slug_header(self):
        h = slug.blank_slug_header()
        for props in ["argle", "clusters", "length", "sha256hash", "zargle", "zzpadding"]:
            self.assertTrue(props in h)

    def test_slug_header_bytes(self):
        h = slug.blank_slug_header()
        h["clusters"] = 1
        h["length"] = 1
        rc = slug.slug_header_bytes(h)
        self.assertEqual(len(rc), 1024)

    def test_extract_slug_header(self):
        h = slug.blank_slug_header()
        h["clusters"] = 1
        h["length"] = 1
        rc = slug.slug_header_bytes(h)
        new_h = slug.extract_slug_header(rc)
        self.assertEqual(h, new_h)

    def test_slug(self):
        data = secrets.token_bytes(1024)

        with open(temp_slug_file, "wb") as f:
            f.write(data)

        my_slug = slug.make_slug(temp_slug_file,)

        self.assertEqual(len(my_slug), 32768)
        self.assertTrue(slug.check_full_slug(my_slug))

        slug.extract_slug(my_slug, temp_extract_file)
        with open(temp_extract_file, "rb") as f:
            extracted_data = f.read()

        self.assertEqual(data, extracted_data)

    def test_slug_encryption(self):
        key_bytes = secrets.token_bytes(32)

        data = secrets.token_bytes(1024)
        with open(temp_slug_file, "wb") as f:
            f.write(data)

        my_slug = slug.make_slug(temp_slug_file)
        encrypted_slug = slug.encrypt_slug(my_slug, key_bytes)
        decrypted_slug = slug.decrypt_slug(encrypted_slug, key_bytes)
        self.assertEqual(my_slug, decrypted_slug)

    def tearDown(self):
        temp_slug_file.unlink(missing_ok=True)
        temp_extract_file.unlink(missing_ok=True)

