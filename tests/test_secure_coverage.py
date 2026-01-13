import json
import os
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.utils.translation import gettext

from migasfree import secure

# Create a temporary directory for keys
TEMP_KEYS_DIR = tempfile.mkdtemp()


@override_settings(MIGASFREE_KEYS_DIR=TEMP_KEYS_DIR)
class SecureTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEMP_KEYS_DIR):
            shutil.rmtree(TEMP_KEYS_DIR)
        super().tearDownClass()

    def setUp(self):
        # Clear cache to avoid side effects
        secure.clear_jwk_cache()
        # Ensure dir exists
        if not os.path.exists(TEMP_KEYS_DIR):
            os.makedirs(TEMP_KEYS_DIR)

    def test_generate_rsa_keys(self):
        name = 'test-keys'
        secure.generate_rsa_keys(name)
        self.assertTrue(os.path.exists(os.path.join(TEMP_KEYS_DIR, f'{name}.pri')))
        self.assertTrue(os.path.exists(os.path.join(TEMP_KEYS_DIR, f'{name}.pub')))

    def test_sign_and_verify(self):
        name = 'test-sign'
        secure.generate_rsa_keys(name)
        data = {'hello': 'world'}

        # Sign
        token = secure.sign(data, f'{name}.pri')
        self.assertIsInstance(token, str)

        # Verify
        payload = secure.verify(token, f'{name}.pub')
        self.assertEqual(payload, json.dumps(data).encode('utf-8'))

    def test_encrypt_and_decrypt(self):
        name = 'test-enc'
        secure.generate_rsa_keys(name)
        data = {'secret': 'data'}

        # Encrypt (encrypts for public key holder)
        token = secure.encrypt(data, f'{name}.pub')
        self.assertIsInstance(token, str)

        # Decrypt (decrypts with private key)
        decrypted = secure.decrypt(token, f'{name}.pri')
        # decrypt returns string (decoded utf-8)
        self.assertEqual(json.loads(decrypted), data)

    def test_wrap_and_unwrap(self):
        sender = 'sender'
        recipient = 'recipient'
        secure.generate_rsa_keys(sender)
        secure.generate_rsa_keys(recipient)

        data = {'transferred': 'data'}

        # Wrap: Sign with Sender Private, Encrypt with Recipient Public
        token = secure.wrap(data, f'{sender}.pri', f'{recipient}.pub')

        # Unwrap: Decrypt with Recipient Private, Verify with Sender Public
        unwrapped_data = secure.unwrap(token, f'{recipient}.pri', f'{sender}.pub')

        self.assertEqual(unwrapped_data, data)

    def test_unwrap_invalid_signature(self):
        sender = 'sender'
        attacker = 'attacker'
        recipient = 'recipient'
        secure.generate_rsa_keys(sender)
        secure.generate_rsa_keys(attacker)
        secure.generate_rsa_keys(recipient)

        data = {'fake': 'data'}

        # Signed by attacker, but claim to be sender
        token = secure.wrap(data, f'{attacker}.pri', f'{recipient}.pub')

        # Recipient tries to unwrap expecting sender signature
        result = secure.unwrap(token, f'{recipient}.pri', f'{sender}.pub')

        self.assertEqual(result, gettext('Invalid Signature'))
