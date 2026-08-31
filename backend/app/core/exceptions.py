# attr: m1
# [custom application exceptions]
from __future__ import annotations

from typing import Any, Optional


class OrcaException(Exception):
    # [base custom exception for backend errors]
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details


class InsufficientInformationError(OrcaException):
    # [raised when safety critical data is unavailable across all tiers]
    def __init__(self, missing_data: Any = None):
        super().__init__(
            message="Cannot safely assess trip — critical data unavailable",
            error_code="INSUFFICIENT_INFORMATION",
            status_code=200,
            details=missing_data,
        )


class AdapterTimeoutError(OrcaException):
    # [raised when upstream data provider times out]
    def __init__(self, adapter_name: str):
        super().__init__(
            message=f"External source timeout: {adapter_name}",
            error_code="UPSTREAM_TIMEOUT",
            status_code=502,
        )


class ValidationError(OrcaException):
    # [raised on request semantic validation failure]
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )
# attr: m1

