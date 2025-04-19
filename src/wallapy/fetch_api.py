"""
Functions for interacting with the Wallapop API.
Includes building search URLs and fetching item data with pagination handling.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode

# --- Use relative imports for modules within the same package ---
from .request_handler import safe_request
from .config import BASE_URL_WALLAPOP
from .utils import clean_text
from .exceptions import WallaPyRequestError, WallaPyParsingError, WallaPyException

logger = logging.getLogger(__name__)


def setup_url(
    product_name: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    order_by: str = "newest",
    time_filter: Optional[str] = None,
) -> str:
    """
    Constructs the initial search URL for the Wallapop API.

    Args:
        product_name: The main product name to search for.
        min_price: Minimum item price. Defaults to None.
        max_price: Maximum item price. Defaults to None.
        order_by: Sorting criteria ('newest', 'price_low_to_high', 'price_high_to_low').
                  Defaults to 'newest'.
        time_filter: Time filter for listings ('today', 'lastWeek', 'lastMonth').
                     Wallapop API seems to use 'publish_date' or similar,
                     needs verification. This implementation uses a placeholder.
                     Defaults to None.

    Returns:
        The constructed URL string for the API request.

    Raises:
        ValueError: If invalid `order_by` or `time_filter` values are provided
                    (currently only logs warnings).
    """

    # Clean inputs
    product_name_cleaned = clean_text(product_name)
    product_name_cleaned = product_name_cleaned.replace(" ", "%20")
    query = product_name_cleaned
    # Ensure base URL doesn't have trailing slash if query starts with ?
    base_url = BASE_URL_WALLAPOP.rstrip("/")
    initial_url = f"{base_url}?source=search_box&keywords={query}"

    # Add price filters (Wallapop API uses integers for price parameters)
    if min_price is not None:
        initial_url += f"&min_sale_price={int(min_price)}"
    if max_price is not None:
        initial_url += f"&max_sale_price={int(max_price)}"

    # Validate and add order_by
    allowed_order_by = ["newest", "price_low_to_high", "price_high_to_low"]
    if order_by in allowed_order_by:
        initial_url += f"&order_by={order_by}"
    else:
        logger.warning(f"Invalid order_by value '{order_by}'. Using default 'newest'.")
        initial_url += "&order_by=newest"  # Default to newest if invalid

    if time_filter:
        initial_url += f"&time_filter={time_filter}"

    logger.debug(f"Constructed URL: {initial_url}")
    return initial_url


def fetch_wallapop_items(
    initial_url: str, headers: Dict[str, str], max_total_items: int
) -> List[Dict[str, Any]]:
    """
    Fetches items from the Wallapop API, handling pagination and item limits.

    Args:
        initial_url: The starting URL for the search (obtained from `setup_url`).
        headers: HTTP headers to use for the requests.
        max_total_items: The maximum number of items to retrieve before stopping.

    Returns:
        A list of raw item data dictionaries fetched from the API.
        Returns an empty list if no items are found or an error occurs.

    Raises:
        WallaPyRequestError: If the initial request or subsequent pagination requests fail after retries.
        WallaPyParsingError: If the API response cannot be parsed or lacks expected structure.
    """
    all_items_data = []
    current_url = initial_url
    page_count = 1
    items_fetched_count = 0
    next_page_cursor = None  # Initialize next_page_cursor

    # Check if initial URL already has a cursor, if not, start from beginning
    parsed_initial_url = urlparse(initial_url)
    initial_query_params = parse_qs(parsed_initial_url.query)
    if "start_cursor" not in initial_query_params:
        pass  # Assuming the initial URL without start_cursor is the first page

    while current_url and items_fetched_count < max_total_items:
        logger.debug(
            f"Fetching page {page_count}. Target items: {max_total_items}. Current count: {items_fetched_count}"
        )
        log_url = current_url[:120] + "..." if len(current_url) > 120 else current_url
        # logger.debug(f"Requesting URL: {log_url}")

        response = safe_request(current_url, headers=headers)

        if response is None:
            error_msg = f"Failed to fetch page {page_count} from {log_url} after multiple retries."
            logger.error(error_msg)
            raise WallaPyRequestError(error_msg)  # Lancia eccezione specifica

        if response.status_code != 200:
            error_msg = (
                f"Failed API request to Wallapop (Page {page_count}). "
                f"Status Code: {response.status_code}. URL: {log_url}"
            )
            logger.error(error_msg)
            try:
                logger.error(f"Response body: {response.text[:500]}...")
            except Exception:
                logger.error("Could not read response body.")
            raise WallaPyRequestError(error_msg)  # Lancia eccezione specifica

        try:
            data = response.json()

            # Navigate through the new structure safely using .get()
            data_section = data.get("data", {})
            section_payload = data_section.get("section", {}).get("payload", {})
            items_on_page = section_payload.get("items", [])

            if not isinstance(items_on_page, list):
                logger.warning(
                    f"Expected list for 'items' in data.section.payload from {log_url}, got {type(items_on_page)}. Treating as empty."
                )
                items_on_page = []

            if items_on_page:
                num_items_on_page = len(items_on_page)
                items_to_add = items_on_page[: max_total_items - items_fetched_count]
                all_items_data.extend(items_to_add)
                items_fetched_count = len(all_items_data)
                # logger.info(
                #     f"  Found {num_items_on_page} items on page {page_count}. Total collected: {items_fetched_count}"
                # )

                if items_fetched_count >= max_total_items:
                    logger.info(
                        f"  Reached item limit ({max_total_items}). Stopping pagination."
                    )
                    current_url = None  # Stop fetching
                    next_page_cursor = None  # Ensure no next page is processed
                else:
                    # Get the next page cursor from the 'meta' section
                    meta_section = data.get("meta", {})
                    next_page_cursor = meta_section.get("next_page")

                    if not next_page_cursor:
                        logger.info(
                            f"No 'next_page' cursor found in meta section from {log_url}. Assuming end of results."
                        )
                        current_url = None  # Stop if no pagination key

            else:
                logger.info(
                    f"  No items found on page {page_count} ({log_url}). Stopping pagination."
                )
                current_url = None
                next_page_cursor = None  # Ensure no next page is processed

            # Prepare next URL if a cursor exists and the limit hasn't been reached
            if next_page_cursor and current_url:
                try:
                    parsed_url = urlparse(current_url)
                    query_params = parse_qs(parsed_url.query)
                    query_params["start_cursor"] = [next_page_cursor]
                    query_params.pop("since", None)
                    query_params.pop("next_page", None)

                    new_query = urlencode(query_params, doseq=True)
                    base_api_url = parsed_url._replace(query="").geturl()
                    current_url = f"{base_api_url}?{new_query}"
                    page_count += 1
                except Exception as e:
                    parse_error_msg = f"Error constructing next page URL from {current_url} with start_cursor={next_page_cursor}: {e}"
                    logger.error(parse_error_msg)
                    current_url = None
            elif current_url and not next_page_cursor and items_on_page:
                logger.info(
                    f"No 'next_page' cursor found in meta section from {log_url}, but items were present. Assuming end of results."
                )
                current_url = None

        except json.JSONDecodeError as e:
            decode_error_msg = f"Error decoding JSON response from {log_url}: {e}. Response text: {response.text[:500]}..."
            logger.error(decode_error_msg)
            raise WallaPyParsingError(
                decode_error_msg
            ) from e  # Lancia eccezione specifica

        except (KeyError, TypeError, IndexError) as e:
            parse_error_msg = f"Error parsing expected data structure from API response ({log_url}): {e}. Response: {response.text[:500]}..."
            logger.error(parse_error_msg)
            raise WallaPyParsingError(
                parse_error_msg
            ) from e  # Lancia eccezione specifica
        except WallaPyRequestError:  # Rilancia le eccezioni già specifiche
            raise
        except Exception as e:
            unexpected_error_msg = (
                f"An unexpected error occurred processing response from {log_url}: {e}"
            )
            logger.exception(unexpected_error_msg)
            raise WallaPyException(
                unexpected_error_msg
            ) from e  # Incapsula in eccezione generica

    if len(all_items_data) > max_total_items:
        logger.warning(
            f"Returned items ({len(all_items_data)}) exceed limit ({max_total_items}). Truncating."
        )
        all_items_data = all_items_data[:max_total_items]

    logger.info(f"Finished fetching. Total items collected: {len(all_items_data)}")
    return all_items_data
