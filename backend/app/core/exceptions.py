"""
Custom exception hierarchy for FraudShield AI.

Services and repositories raise these domain exceptions instead of
generic Python exceptions or HTTPException directly. A single FastAPI
exception handler (registered in main.py) translates them into
consistent JSON error responses at the API boundary. This keeps
HTTP-status concerns out of the service layer.
"""


class FraudShieldError(Exception):
    """Base class for all application-specific errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(FraudShieldError):
    status_code = 404
    error_code = "not_found"


class ValidationError(FraudShieldError):
    status_code = 422
    error_code = "validation_error"


class AuthenticationError(FraudShieldError):
    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(FraudShieldError):
    status_code = 403
    error_code = "authorization_error"


class ConflictError(FraudShieldError):
    status_code = 409
    error_code = "conflict"


class RateLimitExceededError(FraudShieldError):
    status_code = 429
    error_code = "rate_limit_exceeded"


class ModelNotLoadedError(FraudShieldError):
    status_code = 503
    error_code = "model_not_loaded"


class LLMProviderError(FraudShieldError):
    status_code = 502
    error_code = "llm_provider_error"


class PromptInjectionDetectedError(FraudShieldError):
    status_code = 400
    error_code = "prompt_injection_detected"
