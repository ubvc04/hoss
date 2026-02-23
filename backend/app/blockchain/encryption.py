"""
Encryption Utility
AES-256 encryption/decryption for report files before IPFS upload.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from typing import Tuple
from ..config import Config


class EncryptionService:
    """
    AES-256-CBC encryption service for report files.
    Uses a master key from configuration and generates per-file IVs.
    """

    BLOCK_SIZE = 16  # AES block size in bytes
    KEY_SIZE = 32    # 256 bits

    def __init__(self):
        """Initialize encryption service with master key from config."""
        self.master_key = self._load_or_generate_key()

    def _load_or_generate_key(self) -> bytes:
        """Load encryption key from config or generate new one."""
        key_hex = getattr(Config, 'ENCRYPTION_KEY', None)
        if key_hex:
            try:
                return bytes.fromhex(key_hex)
            except ValueError:
                pass
        
        # Generate a new key (should be saved to config in production)
        # WARNING: In production, this key MUST be persistent!
        return os.urandom(self.KEY_SIZE)

    def encrypt_file(self, file_data: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt file data using AES-256-CBC.
        
        Args:
            file_data: Raw file bytes to encrypt
            
        Returns:
            Tuple of (encrypted_data, iv)
        """
        # Generate random IV for this file
        iv = os.urandom(self.BLOCK_SIZE)

        # Pad data to block size
        padder = padding.PKCS7(self.BLOCK_SIZE * 8).padder()
        padded_data = padder.update(file_data) + padder.finalize()

        # Encrypt
        cipher = Cipher(
            algorithms.AES(self.master_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        return encrypted, iv

    def decrypt_file(self, encrypted_data: bytes, iv: bytes) -> bytes:
        """
        Decrypt file data using AES-256-CBC.
        
        Args:
            encrypted_data: Encrypted file bytes
            iv: Initialization vector used during encryption
            
        Returns:
            Decrypted file bytes
        """
        # Decrypt
        cipher = Cipher(
            algorithms.AES(self.master_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Remove padding
        unpadder = padding.PKCS7(self.BLOCK_SIZE * 8).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data

    def encrypt_and_encode(self, file_data: bytes) -> str:
        """
        Encrypt file and return base64-encoded result with IV prepended.
        
        Args:
            file_data: Raw file bytes
            
        Returns:
            Base64-encoded string with format: base64(IV + encrypted_data)
        """
        encrypted, iv = self.encrypt_file(file_data)
        # Prepend IV to encrypted data
        combined = iv + encrypted
        return base64.b64encode(combined).decode('utf-8')

    def decode_and_decrypt(self, encoded_data: str) -> bytes:
        """
        Decode base64 data and decrypt file.
        
        Args:
            encoded_data: Base64-encoded string with IV prepended
            
        Returns:
            Decrypted file bytes
        """
        combined = base64.b64decode(encoded_data)
        # Extract IV and encrypted data
        iv = combined[:self.BLOCK_SIZE]
        encrypted = combined[self.BLOCK_SIZE:]
        return self.decrypt_file(encrypted, iv)

    def encrypt_for_storage(self, file_data: bytes) -> Tuple[bytes, str]:
        """
        Encrypt file and return encrypted bytes and IV as hex string.
        Use this when storing IV separately.
        
        Args:
            file_data: Raw file bytes
            
        Returns:
            Tuple of (encrypted_bytes, iv_hex_string)
        """
        encrypted, iv = self.encrypt_file(file_data)
        return encrypted, iv.hex()

    def decrypt_from_storage(self, encrypted_data: bytes, iv_hex: str) -> bytes:
        """
        Decrypt file using separately stored IV.
        
        Args:
            encrypted_data: Encrypted file bytes
            iv_hex: IV as hex string
            
        Returns:
            Decrypted file bytes
        """
        iv = bytes.fromhex(iv_hex)
        return self.decrypt_file(encrypted_data, iv)


# Singleton instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """Get singleton encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def generate_encryption_key() -> str:
    """
    Generate a new encryption key for configuration.
    Call this once and save the result to ENCRYPTION_KEY in config.
    """
    return os.urandom(EncryptionService.KEY_SIZE).hex()
