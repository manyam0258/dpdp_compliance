import frappe
import unittest
from dpdp_compliance.utils.encryption import encrypt_data, decrypt_data


class TestEncryption(unittest.TestCase):
    def test_encryption_flow(self):
        original_text = "SensitiveAADHAAR-1234"

        # 1. Encrypt
        encrypted = encrypt_data(original_text)
        self.assertNotEqual(original_text, encrypted)
        self.assertTrue(len(encrypted) > len(original_text))
        print(f"\n[Test] Encrypted '{original_text}' -> '{encrypted}'")

        # 2. Decrypt
        decrypted = decrypt_data(encrypted)
        self.assertEqual(original_text, decrypted)
        print(f"[Test] Decrypted '{encrypted}' -> '{decrypted}'")


def run_test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEncryption)
    unittest.TextTestRunner(verbosity=2).run(suite)
