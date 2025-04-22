# filepath: /Users/duccio/Documents/GitHub/WallaPy/src/wallapy/__init__.py
__version__ = "0.6.0"  # Core is async, sync wrapper provided

import asyncio  # Add asyncio import
import logging  # Import the logging module
from typing import List, Dict, Any, Optional  # Add imports for type hints

from .check import WallaPyClient  # Import the client class
from .exceptions import (
    WallaPyException,
    WallaPyRequestError,
    WallaPyParsingError,
    WallaPyConfigurationError,
)


# Define the synchronous convenience function using an internal client and asyncio.run()
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
    deep_search: bool = True,  # Add deep_search parameter
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper to search Wallapop.

    This function provides a simple, synchronous interface. It internally creates a
    WallaPyClient and runs its asynchronous check_wallapop method using asyncio.run().

    For advanced usage or integration into existing async applications,
    instantiate WallaPyClient directly and use its async methods.

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
        deep_search: Fetch detailed information for each item. Defaults to True.

    Returns:
        A list of dictionaries representing matching products.

    Raises:
        WallaPyConfigurationError: If input parameters like price range are invalid.
        WallaPyRequestError: If API requests fail after retries.
        WallaPyParsingError: If the API response cannot be parsed.
        WallaPyException: For other unexpected errors during the process.
    """
    # Configure the asyncio logger based on verbosity to hide selector messages
    asyncio_logger = logging.getLogger("asyncio")
    original_level = asyncio_logger.level  # Save the original level (optional)

    if verbose < 2:  # If verbosity is less than DEBUG (i.e., WARN or INFO)
        # Temporarily set the asyncio logger level to INFO to hide DEBUG messages
        asyncio_logger.setLevel(logging.INFO)

    # Create a temporary client instance for this call
    client = WallaPyClient()

    # Run the async check_wallapop method within the sync function
    try:
        # Use asyncio.run to execute the async method
        results = asyncio.run(
            client.check_wallapop(
                product_name=product_name,
                keywords=keywords,
                min_price=min_price,
                max_price=max_price,
                excluded_keywords=excluded_keywords,
                max_total_items=max_total_items,
                order_by=order_by,
                time_filter=time_filter,
                verbose=verbose,  # Pass verbose to the async method
                deep_search=deep_search,
            )
        )
        return results
    except RuntimeError as e:
        # Handle cases where asyncio.run cannot be called (e.g., nested event loops)
        if "cannot be called from a running event loop" in str(e):
            raise RuntimeError(
                "The synchronous check_wallapop wrapper cannot be called from within an existing asyncio event loop. "
                "Instantiate WallaPyClient and use its async check_wallapop method directly in async code."
            ) from e
        else:
            raise  # Re-raise other runtime errors
    finally:
        # Restore the original level of the asyncio logger (optional, but good practice)
        asyncio_logger.setLevel(original_level)


# Expose the client class, the convenience function, and exceptions
__all__ = [
    "WallaPyClient",  # Expose the class for advanced users
    "check_wallapop",  # Expose the synchronous convenience function
    "WallaPyException",
    "WallaPyRequestError",
    "WallaPyParsingError",
    "WallaPyConfigurationError",
]
