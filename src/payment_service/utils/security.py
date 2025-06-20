"""Security utilities and middleware."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import structlog
from payment_service.config import settings


class SecurityManager:
    """Security utilities for the payment service."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def generate_token(self, payload: Dict[str, Any], expiry_hours: int = 24) -> str:
        """Generate a secure token with payload and expiry."""
        # In production, use proper JWT library
        import json
        import base64

        # Create payload with expiry
        token_payload = {
            **payload,
            "exp": (datetime.utcnow() + timedelta(hours=expiry_hours)).timestamp(),
            "iat": datetime.utcnow().timestamp(),
        }

        # Encode payload
        payload_json = json.dumps(token_payload, sort_keys=True)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        # Create signature
        signature = self._create_signature(payload_b64)

        return f"{payload_b64}.{signature}"

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token and return payload if valid."""
        try:
            import json
            import base64

            # Split token
            parts = token.split(".")
            if len(parts) != 2:
                return None

            payload_b64, signature = parts

            # Verify signature
            expected_signature = self._create_signature(payload_b64)
            if not hmac.compare_digest(signature, expected_signature):
                self.logger.warning("Invalid token signature")
                return None

            # Decode payload
            payload_json = base64.b64decode(payload_b64.encode()).decode()
            payload = json.loads(payload_json)

            # Check expiry
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                self.logger.warning("Token expired")
                return None

            return payload

        except Exception as e:
            self.logger.warning("Token validation error", error=str(e))
            return None

    def _create_signature(self, payload: str) -> str:
        """Create HMAC signature for payload."""
        return hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for comparison."""
        salt = settings.secret_key.encode()
        return hashlib.pbkdf2_hmac("sha256", data.encode(), salt, 100000).hex()

    def verify_sensitive_data(self, data: str, hashed: str) -> bool:
        """Verify sensitive data against hash."""
        return hmac.compare_digest(self.hash_sensitive_data(data), hashed)

    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", '"', "'", "&", ";", "|", "`", "$"]
        sanitized = input_str

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized.strip()

    def is_valid_merchant_id(self, merchant_id: str) -> bool:
        """Validate merchant ID format."""
        # Basic validation - in production, check against merchant database
        if not merchant_id or len(merchant_id) < 3:
            return False

        # Check for valid characters (alphanumeric and underscores)
        return merchant_id.replace("_", "").isalnum()

    def rate_limit_key(self, identifier: str, window: str = "minute") -> str:
        """Generate rate limiting key."""
        current_time = datetime.utcnow()

        if window == "minute":
            time_window = current_time.strftime("%Y-%m-%d-%H-%M")
        elif window == "hour":
            time_window = current_time.strftime("%Y-%m-%d-%H")
        else:
            time_window = current_time.strftime("%Y-%m-%d")

        return f"rate_limit:{identifier}:{time_window}"


# Global security manager instance
security_manager = SecurityManager()
