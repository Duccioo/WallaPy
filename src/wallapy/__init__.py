# filepath: /Users/duccio/Documents/GitHub/WallaPy/src/wallapy/__init__.py
__version__ = "0.1.0"

from typing import List, Dict, Any, Optional  # Add imports for type hints

from .check import WallaPyClient  # Import the client class
from .exceptions import (
    WallaPyException,
    WallaPyRequestError,
    WallaPyParsingError,
    WallaPyConfigurationError,
)

# Create a default client instance for simple usage
_default_client = WallaPyClient()


# Define the convenience function using the default client
def check_wallapop(
    product_name: str,
    keywords: Optional[List[str]] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    excluded_keywords: Optional[List[str]] = None,
    max_total_items: int = 100,
    order_by: str = "newest",
    time_filter: Optional[str] = None,
    verbose: int = 0,
) -> List[Dict[str, Any]]:
    """
    Searches Wallapop using default configurations.

    This is a convenience function that uses a pre-configured WallaPyClient.
    For custom configurations (location, headers, etc.), instantiate WallaPyClient directly.

    Args:
        product_name: The primary name of the product to search for.
        keywords: Additional keywords to refine the search. Defaults to None.
        min_price: Minimum price filter. Defaults to None.
        max_price: Maximum price filter. Defaults to None.
        excluded_keywords: List of keywords to exclude from results. Defaults to None.
        max_total_items: Maximum number of items to fetch from the API. Defaults to 100.
        order_by: Sorting order ('newest', 'price_low_to_high', 'price_high_to_low').
                  Defaults to 'newest'.
        time_filter: Time filter ('today', 'lastWeek', 'lastMonth'). Needs API verification.
                     Defaults to None.
        verbose: Controls logging verbosity (0=WARN, 1=INFO, 2=DEBUG).

    Returns:
        A list of dictionaries representing matching products.

    Raises:
        WallaPyConfigurationError: If input parameters like price range are invalid.
        WallaPyRequestError: If API requests fail after retries.
        WallaPyParsingError: If the API response cannot be parsed.
        WallaPyException: For other unexpected errors during the process.
    """
    return _default_client.check_wallapop(
        product_name=product_name,
        keywords=keywords,
        min_price=min_price,
        max_price=max_price,
        excluded_keywords=excluded_keywords,
        max_total_items=max_total_items,
        order_by=order_by,
        time_filter=time_filter,
        verbose=verbose,
    )


# Expose the client class, the convenience function, and exceptions
__all__ = [
    "WallaPyClient",  # Expose the class for advanced users
    "check_wallapop",  # Expose the convenience function
    "WallaPyException",
    "WallaPyRequestError",
    "WallaPyParsingError",
    "WallaPyConfigurationError",
]
