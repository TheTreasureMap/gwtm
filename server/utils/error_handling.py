from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional, Union


class ErrorDetail:
    """Standardized error detail structure"""

    def __init__(self,
                 message: str,
                 code: str = None,
                 params: Dict[str, Any] = None):
        self.message = message
        self.code = code
        self.params = params or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {"message": self.message}
        if self.code:
            result["code"] = self.code
        if self.params:
            result["params"] = self.params
        return result


def validation_exception(
        message: str = "Validation error",
        errors: List[Union[str, Dict, ErrorDetail]] = None
) -> HTTPException:
    """Create a standardized validation error exception"""
    detail = {"message": message}

    if errors:
        formatted_errors = []
        for error in errors:
            if isinstance(error, str):
                formatted_errors.append({"message": error})
            elif isinstance(error, ErrorDetail):
                formatted_errors.append(error.to_dict())
            elif isinstance(error, dict):
                formatted_errors.append(error)
        detail["errors"] = formatted_errors

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )


def permission_exception(message: str = "Permission denied") -> HTTPException:
    """Create a standardized permission error exception"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"message": message}
    )


def not_found_exception(message: str = "Resource not found") -> HTTPException:
    """Create a standardized not found exception"""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"message": message}
    )


def server_exception(message: str = "Internal server error") -> HTTPException:
    """Create a standardized server error exception"""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"message": message}
    )


def conflict_exception(message: str = "Resource conflict") -> HTTPException:
    """Create a standardized conflict exception"""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"message": message}
    )
