"""Custom exceptions for the payment service."""

from typing import Optional, Dict, Any


class PaymentServiceException(Exception):
    """Base exception for payment service."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "PAYMENT_SERVICE_ERROR"
        self.details = details or {}


class ValidationError(PaymentServiceException):
    """Raised when input validation fails."""

    def __init__(
        self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class PaymentProcessingError(PaymentServiceException):
    """Raised when payment processing fails."""

    def __init__(
        self,
        message: str,
        transaction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "PAYMENT_PROCESSING_ERROR", details)
        self.transaction_id = transaction_id


class RefundProcessingError(PaymentServiceException):
    """Raised when refund processing fails."""

    def __init__(
        self,
        message: str,
        refund_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "REFUND_PROCESSING_ERROR", details)
        self.refund_id = refund_id
        self.transaction_id = transaction_id


class AuthenticationError(PaymentServiceException):
    """Raised when authentication fails."""

    def __init__(
        self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(PaymentServiceException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Authorization failed",
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTHORIZATION_ERROR", details)
        self.resource = resource


class DatabaseError(PaymentServiceException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "DATABASE_ERROR", details)
        self.operation = operation


class ExternalServiceError(PaymentServiceException):
    """Raised when external service calls fail."""

    def __init__(
        self, message: str, service: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)
        self.service = service


class ConfigurationError(PaymentServiceException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_key = config_key


class RateLimitError(PaymentServiceException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "RATE_LIMIT_ERROR", details)
        self.limit = limit
        self.window = window


class TransactionNotFoundError(PaymentServiceException):
    """Raised when transaction is not found."""

    def __init__(self, transaction_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Transaction {transaction_id} not found"
        super().__init__(message, "TRANSACTION_NOT_FOUND", details)
        self.transaction_id = transaction_id


class InvalidTransactionStateError(PaymentServiceException):
    """Raised when transaction is in invalid state for operation."""

    def __init__(
        self,
        transaction_id: str,
        current_state: str,
        required_state: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Transaction {transaction_id} is in state '{current_state}' but requires '{required_state}'"
        super().__init__(message, "INVALID_TRANSACTION_STATE", details)
        self.transaction_id = transaction_id
        self.current_state = current_state
        self.required_state = required_state


class EncryptionError(PaymentServiceException):
    """Raised when encryption/decryption fails."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "ENCRYPTION_ERROR", details)
        self.operation = operation


class CacheError(PaymentServiceException):
    """Raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "CACHE_ERROR", details)
        self.operation = operation
        self.key = key
