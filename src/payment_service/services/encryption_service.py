"""Encryption service for sensitive data handling."""

import base64
import json
from typing import Dict, Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

from payment_service.config import settings
from payment_service.models.payment import CardData


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._cipher = self._create_cipher()

    def _create_cipher(self) -> Fernet:
        """Create encryption cipher from configuration."""
        # In production, use a proper key derivation function
        # For demo purposes, we'll use a simple approach
        key = settings.encryption_key.encode()

        # Pad or truncate key to 32 bytes for Fernet
        if len(key) < 32:
            key = key.ljust(32, b"0")
        elif len(key) > 32:
            key = key[:32]

        # Use PBKDF2 to derive a proper key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"payment_service_salt",  # In production, use a random salt
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))

        return Fernet(derived_key)

    def encrypt_card_data(self, card_data: CardData) -> str:
        """Encrypt card data for secure storage."""
        try:
            # Convert card data to dict, excluding sensitive fields from logs
            card_dict = {
                "card_number": card_data.card_number,
                "expiry_month": card_data.expiry_month,
                "expiry_year": card_data.expiry_year,
                "cvv": card_data.cvv,
                "cardholder_name": card_data.cardholder_name,
            }

            # Serialize to JSON
            card_json = json.dumps(card_dict)

            # Encrypt
            encrypted_data = self._cipher.encrypt(card_json.encode())

            # Return base64 encoded string
            return base64.b64encode(encrypted_data).decode()

        except Exception as e:
            self.logger.error("Failed to encrypt card data", error=str(e))
            raise

    def decrypt_card_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt card data from storage."""
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())

            # Decrypt
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)

            # Parse JSON
            card_dict = json.loads(decrypted_bytes.decode())

            return card_dict

        except Exception as e:
            self.logger.error("Failed to decrypt card data", error=str(e))
            raise

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt any sensitive string data."""
        try:
            encrypted_data = self._cipher.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error("Failed to encrypt sensitive data", error=str(e))
            raise

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive string data."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            self.logger.error("Failed to decrypt sensitive data", error=str(e))
            raise

    def get_card_last_four(self, card_number: str) -> str:
        """Safely extract last four digits of card number."""
        return card_number[-4:] if len(card_number) >= 4 else card_number

    def mask_card_number(self, card_number: str) -> str:
        """Mask card number for logging/display."""
        if len(card_number) <= 4:
            return "*" * len(card_number)

        return "*" * (len(card_number) - 4) + card_number[-4:]
