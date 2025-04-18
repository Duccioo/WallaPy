# filepath: /Users/duccio/Documents/GitHub/WallaPy/src/wallapy/__init__.py
__version__ = "0.1.0"

from .check import check_wallapop
from .exceptions import (
    WallaPyException,
    WallaPyRequestError,
    WallaPyParsingError,
    WallaPyConfigurationError,
)


# Expose main function and exceptions
__all__ = [
    "check_wallapop",
    "WallaPyException",
    "WallaPyRequestError",
    "WallaPyParsingError",
    "WallaPyConfigurationError",
]
