"""
Academic Command Center - Encryption Service
Handles encryption and decryption of sensitive data (API keys, tokens)
using AES-256-CBC encryption.
"""

import os
import base64
import hashlib
import secrets
import json
from typing import Tuple, Optional
from pathlib import Path
import logging

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Encryption service for protecting sensitive data.

    Uses AES-256-CBC with unique IV per encryption.
    Master key is stored in config/encryption.key
    """

    def __init__(self, config_dir: str = r"C:\Users\Gamer\Getitdone\config"):
        """
        Initialize encryption service.

        Args:
            config_dir: Directory to store encryption key
        """
        self.config_dir = config_dir
        self.key_file_path = os.path.join(config_dir, "encryption.key")

        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)

        # Load or generate master key
        self.master_key = self._load_or_generate_master_key()

    def _load_or_generate_master_key(self) -> bytes:
        """
        Load existing master key or generate new one.

        Returns:
            32-byte master key
        """
        if os.path.exists(self.key_file_path):
            # Load existing key
            try:
                with open(self.key_file_path, 'rb') as f:
                    key_data = f.read()

                # Decode from base64
                master_key = base64.b64decode(key_data)

                if len(master_key) != 32:
                    raise ValueError("Invalid master key length")

                logger.info("Master key loaded from file")
                return master_key

            except Exception as e:
                logger.error(f"Failed to load master key: {e}")
                logger.info("Generating new master key...")
                return self._generate_new_master_key()
        else:
            # Generate new key
            return self._generate_new_master_key()

    def _generate_new_master_key(self) -> bytes:
        """
        Generate new 256-bit master key.

        Returns:
            32-byte master key
        """
        # Generate cryptographically secure random key
        master_key = secrets.token_bytes(32)  # 256 bits

        # Save to file (base64 encoded for readability)
        try:
            with open(self.key_file_path, 'wb') as f:
                f.write(base64.b64encode(master_key))

            # Set file permissions (read-only for owner on Windows)
            if os.name == 'nt':  # Windows
                import win32security
                import ntsecuritycon as con

                # Get current user
                user, domain, type_unused = win32security.LookupAccountName("", os.getlogin())

                # Create security descriptor
                sd = win32security.SECURITY_DESCRIPTOR()
                dacl = win32security.ACL()

                # Add ACE (Access Control Entry) for current user only
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_GENERIC_READ,
                    user
                )

                sd.SetSecurityDescriptorDacl(1, dacl, 0)

                # Apply to file
                win32security.SetFileSecurity(
                    self.key_file_path,
                    win32security.DACL_SECURITY_INFORMATION,
                    sd
                )

                logger.info("File permissions set (Windows)")

            logger.info(f"New master key generated and saved to {self.key_file_path}")
            logger.warning("⚠️  IMPORTANT: Backup this file! If lost, encrypted data cannot be recovered.")

            return master_key

        except Exception as e:
            logger.error(f"Failed to save master key: {e}")
            raise

    def encrypt(self, plaintext: str) -> Tuple[bytes, bytes]:
        """
        Encrypt plaintext using AES-256-CBC.

        Args:
            plaintext: String to encrypt

        Returns:
            Tuple of (ciphertext, iv)
        """
        try:
            # Generate random IV (16 bytes for AES)
            iv = secrets.token_bytes(16)

            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.master_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Pad plaintext to block size (AES block size is 128 bits = 16 bytes)
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()

            # Encrypt
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            logger.debug(f"Encrypted {len(plaintext)} characters")
            return ciphertext, iv

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: bytes, iv: bytes) -> str:
        """
        Decrypt ciphertext using AES-256-CBC.

        Args:
            ciphertext: Encrypted data
            iv: Initialization vector used for encryption

        Returns:
            Decrypted plaintext string
        """
        try:
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.master_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()

            # Decode to string
            plaintext = plaintext_bytes.decode('utf-8')

            logger.debug(f"Decrypted {len(plaintext)} characters")
            return plaintext

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_to_hex(self, plaintext: str) -> Tuple[str, str]:
        """
        Encrypt and return as hex strings (for database storage).

        Args:
            plaintext: String to encrypt

        Returns:
            Tuple of (ciphertext_hex, iv_hex)
        """
        ciphertext, iv = self.encrypt(plaintext)
        return ciphertext.hex(), iv.hex()

    def decrypt_from_hex(self, ciphertext_hex: str, iv_hex: str) -> str:
        """
        Decrypt from hex strings.

        Args:
            ciphertext_hex: Hex-encoded ciphertext
            iv_hex: Hex-encoded IV

        Returns:
            Decrypted plaintext
        """
        ciphertext = bytes.fromhex(ciphertext_hex)
        iv = bytes.fromhex(iv_hex)
        return self.decrypt(ciphertext, iv)

    def hash_data(self, data: str) -> str:
        """
        Create SHA256 hash of data (for cache keys, verification).

        Args:
            data: Data to hash

        Returns:
            Hex-encoded hash
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def generate_cache_key(self, *components) -> str:
        """
        Generate cache key from multiple components.

        Args:
            *components: Variable number of strings to combine

        Returns:
            Cache key (SHA256 hash)
        """
        combined = "_".join(str(c) for c in components)
        return self.hash_data(combined)

    def verify_master_key(self) -> bool:
        """
        Verify master key is valid and accessible.

        Returns:
            True if master key is valid
        """
        try:
            # Test encryption/decryption
            test_data = "test_encryption_12345"
            ciphertext, iv = self.encrypt(test_data)
            decrypted = self.decrypt(ciphertext, iv)

            if decrypted == test_data:
                logger.info("Master key verification: PASSED ✓")
                return True
            else:
                logger.error("Master key verification: FAILED ✗")
                return False

        except Exception as e:
            logger.error(f"Master key verification failed: {e}")
            return False

    def rotate_master_key(self, new_key: Optional[bytes] = None) -> bytes:
        """
        Rotate (replace) master key.

        WARNING: All data encrypted with old key must be re-encrypted!

        Args:
            new_key: New master key (if None, generates random key)

        Returns:
            New master key
        """
        logger.warning("⚠️  Master key rotation initiated!")

        # Backup old key
        backup_path = self.key_file_path + ".backup"
        if os.path.exists(self.key_file_path):
            import shutil
            shutil.copy2(self.key_file_path, backup_path)
            logger.info(f"Old key backed up to {backup_path}")

        # Generate or use provided key
        if new_key is None:
            new_key = secrets.token_bytes(32)
            logger.info("Generated new random master key")
        else:
            if len(new_key) != 32:
                raise ValueError("New key must be 32 bytes")
            logger.info("Using provided master key")

        # Save new key
        with open(self.key_file_path, 'wb') as f:
            f.write(base64.b64encode(new_key))

        # Update instance variable
        old_key = self.master_key
        self.master_key = new_key

        logger.info("Master key rotated successfully")
        logger.warning("⚠️  You must re-encrypt all existing encrypted data!")

        return new_key

    def export_key(self, export_path: str, password: str) -> None:
        """
        Export master key to encrypted backup file.

        Args:
            export_path: Where to save encrypted key
            password: Password to protect the export
        """
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'acc_key_export_salt',  # Static salt for key derivation
            iterations=100000,
            backend=default_backend()
        )
        password_key = kdf.derive(password.encode('utf-8'))

        # Encrypt master key with password-derived key
        iv = secrets.token_bytes(16)
        cipher = Cipher(
            algorithms.AES(password_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(128).padder()
        padded_key = padder.update(self.master_key) + padder.finalize()
        encrypted_key = encryptor.update(padded_key) + encryptor.finalize()

        # Save to file
        export_data = {
            'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'info': 'Academic Command Center - Master Key Export'
        }

        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Master key exported to {export_path}")
        logger.info("Keep this file and password safe!")

    def import_key(self, import_path: str, password: str) -> None:
        """
        Import master key from encrypted backup file.

        Args:
            import_path: Path to exported key file
            password: Password used during export
        """
        # Read export file
        with open(import_path, 'r') as f:
            export_data = json.load(f)

        encrypted_key = base64.b64decode(export_data['encrypted_key'])
        iv = base64.b64decode(export_data['iv'])

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'acc_key_export_salt',
            iterations=100000,
            backend=default_backend()
        )
        password_key = kdf.derive(password.encode('utf-8'))

        # Decrypt master key
        cipher = Cipher(
            algorithms.AES(password_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        padded_key = decryptor.update(encrypted_key) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        master_key = unpadder.update(padded_key) + unpadder.finalize()

        # Verify it's 32 bytes
        if len(master_key) != 32:
            raise ValueError("Imported key has invalid length")

        # Save to key file
        with open(self.key_file_path, 'wb') as f:
            f.write(base64.b64encode(master_key))

        # Update instance
        self.master_key = master_key

        logger.info(f"Master key imported from {import_path}")


# ============================================
# Convenience Functions
# ============================================

def secure_delete_file(file_path: str) -> None:
    """
    Securely delete file by overwriting with random data.

    Args:
        file_path: File to delete
    """
    if not os.path.exists(file_path):
        return

    try:
        # Get file size
        file_size = os.path.getsize(file_path)

        # Overwrite with random data (3 passes)
        for _ in range(3):
            with open(file_path, 'wb') as f:
                f.write(secrets.token_bytes(file_size))

        # Delete file
        os.remove(file_path)
        logger.info(f"Securely deleted: {file_path}")

    except Exception as e:
        logger.error(f"Secure delete failed: {e}")
        raise


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.

    Args:
        length: Number of bytes

    Returns:
        Hex-encoded token
    """
    return secrets.token_hex(length)


if __name__ == "__main__":
    # Test encryption service
    print("Testing Encryption Service...")

    # Use test config directory
    test_config_dir = r"C:\Users\Gamer\Getitdone\config_test"
    os.makedirs(test_config_dir, exist_ok=True)

    encryption = EncryptionService(test_config_dir)

    # Test encryption/decryption
    test_api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"

    print(f"\nOriginal: {test_api_key}")

    # Encrypt
    ciphertext_hex, iv_hex = encryption.encrypt_to_hex(test_api_key)
    print(f"Encrypted (hex): {ciphertext_hex[:32]}... (truncated)")
    print(f"IV (hex): {iv_hex}")

    # Decrypt
    decrypted = encryption.decrypt_from_hex(ciphertext_hex, iv_hex)
    print(f"Decrypted: {decrypted}")

    # Verify
    if decrypted == test_api_key:
        print("✓ Encryption/Decryption test PASSED")
    else:
        print("✗ Encryption/Decryption test FAILED")

    # Verify master key
    is_valid = encryption.verify_master_key()
    print(f"\nMaster Key Valid: {is_valid}")

    # Generate cache key
    cache_key = encryption.generate_cache_key("task_type", "user_123", "prompt_text")
    print(f"\nCache Key: {cache_key}")

    print("\nEncryption Service test completed!")
