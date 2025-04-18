"""
Custom exceptions for the WallaPy library.
"""


class WallaPyException(Exception):
    """Base exception class for WallaPy errors."""

    pass


class WallaPyRequestError(WallaPyException):
    """Raised when an API request fails after retries."""

    pass


class WallaPyParsingError(WallaPyException):
    """Raised when the API response cannot be parsed or lacks expected structure."""

    pass


class WallaPyConfigurationError(WallaPyException, ValueError):
    """Raised for invalid configuration parameters (e.g., negative price). Inherits from ValueError for compatibility."""

    pass
