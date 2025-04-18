"""
Core logic for searching and processing Wallapop items.

Provides functions to orchestrate the search based on criteria,
process individual items, and filter them according to requirements.
"""

from fuzzywuzzy import fuzz
import datetime
import logging
from typing import List, Dict, Any, Optional

# --- Use relative imports for modules within the same package ---
from .utils import clean_text, contains_excluded_terms, make_link, validate_prices, tmz
from .fetch_api import fetch_wallapop_items, setup_url
from .config import FUZZY_THRESHOLDS, HEADERS
from .exceptions import WallaPyConfigurationError  # Importa l'eccezione corretta

logger = logging.getLogger(__name__)


def process_wallapop_item(
    item: Dict[str, Any],
    search_product_name: str,  # Renamed for clarity
    search_keywords: List[str],  # Renamed for clarity
    min_price: Optional[float],
    max_price: Optional[float],
    excluded_keywords: List[str],
) -> Optional[Dict[str, Any]]:
    """
    Processes a single raw item dictionary from the Wallapop API.

    Validates the item, extracts relevant fields, performs filtering based on
    keywords, price, excluded terms, and reservation status. Returns a
    formatted dictionary if the item is valid and matches criteria, otherwise None.

    Args:
        item: The raw dictionary representing a Wallapop item.
        search_product_name: The original product name used in the search.
        search_keywords: The list of keywords used in the search.
        min_price: The minimum price filter.
        max_price: The maximum price filter.
        excluded_keywords: A list of keywords that disqualify an item.

    Returns:
        A dictionary containing formatted item details if it passes all checks,
        otherwise None.
    """
    try:
        # --- Essential Fields Extraction ---
        product_id = item.get("id")
        if not product_id:
            logger.debug("Skipping item due to missing ID.")
            return None  # Skip items without an ID

        product_title = item.get("title")
        product_description = item.get("description")
        web_slug = item.get("web_slug")
        price_data = item.get("price", {})
        product_price = price_data.get("amount")
        product_currency = price_data.get("currency")
        user_id = item.get("user_id")
        location_data = item.get("location", {})
        product_location_info = (
            location_data.get("city")
            or location_data.get("region")
            or location_data.get("country_code")
        )
        is_reserved = item.get("flags", {}).get("reserved", False)

        # --- Basic Validation ---
        if not all(
            [
                product_title,
                product_description,
                product_price is not None,
                web_slug,
                user_id,
                product_location_info,
            ]
        ):
            logger.debug(
                f"Item {product_id}: Missing essential data (Title, Desc, Price, Slug, UserID, Location). Skipping."
            )
            return None

        # --- Date Parsing ---
        timestamp_ms = item.get("created_at")
        product_date_utc = None
        if timestamp_ms:
            try:
                product_date_utc = datetime.datetime.fromtimestamp(
                    timestamp_ms / 1000, tz=datetime.timezone.utc
                )
            except (TypeError, ValueError):
                logger.warning(
                    f"Item {product_id}: Invalid timestamp format ({timestamp_ms}). Cannot parse date."
                )
        else:
            logger.warning(f"Item {product_id}: Missing creation/modification date.")

        # --- Filtering Logic ---

        # 1. Price Range Filter
        price_in_range = True
        if min_price is not None and product_price < min_price:
            price_in_range = False
        if max_price is not None and product_price > max_price:
            price_in_range = False

        # 2. Reserved Filter
        if is_reserved:
            logger.debug(f"Item {product_id}: Skipping because it is reserved.")
            return None

        # 3. Excluded Keywords Filter
        full_text_for_exclusion = f"{product_title} {product_description}"
        if contains_excluded_terms(
            full_text_for_exclusion, excluded_keywords, FUZZY_THRESHOLDS["excluded"]
        ):
            logger.debug(f"Item {product_id}: Skipping due to excluded keyword match.")
            return None

        # 4. Keyword Matching (Fuzzy)
        title_cleaned = clean_text(product_title)
        description_cleaned = clean_text(product_description)
        matched_in_description = False
        highest_match_score = 0
        keyword_match_found = False

        if not search_keywords:
            keyword_match_found = True
        else:
            all_scores = []
            for kw in search_keywords:
                title_score = fuzz.partial_ratio(kw, title_cleaned)
                desc_score = fuzz.partial_ratio(kw, description_cleaned)
                all_scores.append(title_score)
                all_scores.append(desc_score)

                if title_score > FUZZY_THRESHOLDS["title"]:
                    keyword_match_found = True
                    highest_match_score = max(highest_match_score, title_score)

                if desc_score > FUZZY_THRESHOLDS["description"]:
                    keyword_match_found = True
                    matched_in_description = True
                    highest_match_score = max(highest_match_score, desc_score)

            if not keyword_match_found:
                logger.debug(
                    f"Item {product_id}: Skipping, no keyword match above threshold. Max score: {max(all_scores) if all_scores else 0}"
                )
                return None

        # --- Apply Filters ---
        if not price_in_range:
            logger.debug(
                f"Item {product_id}: Skipping, price {product_price} out of range ({min_price}-{max_price})."
            )
            return None

        # --- Image Extraction ---
        images_data = item.get("images", [])
        main_image_url = None
        all_image_urls = []
        if images_data and isinstance(images_data, list):
            try:
                main_image_url = (
                    images_data[0].get("urls", {}).get("big")
                    or images_data[0].get("urls", {}).get("medium")
                    or images_data[0].get("urls", {}).get("original")
                    or images_data[0].get("urls", {}).get("small")
                )

                for img_data in images_data:
                    urls = img_data.get("urls", {})
                    img_url = (
                        urls.get("big")
                        or urls.get("medium")
                        or urls.get("original")
                        or urls.get("small")
                    )
                    if img_url:
                        all_image_urls.append(img_url)
            except (IndexError, KeyError, TypeError) as e:
                logger.warning(f"Item {product_id}: Error extracting images: {e}")
                main_image_url = None
                all_image_urls = []

        # --- Seller Link ---
        seller_link = f"https://it.wallapop.com/user/{user_id}" if user_id else None

        # --- Format Output Dictionary ---
        product_date_local = (
            product_date_utc.astimezone(tmz) if product_date_utc else None
        )

        processed_item = {
            "search_term": search_product_name,
            "title": product_title,
            "price": product_price,
            "currency": product_currency,
            "location": product_location_info,
            "description": product_description,
            "link": make_link(web_slug),
            "id": product_id,
            "creation_date_utc": product_date_utc,
            "creation_date_local": product_date_local,
            "seller_platform": "WALLAPOP",
            "seller_link": seller_link,
            "is_reserved": is_reserved,
            "main_image": main_image_url,
            "all_images": all_image_urls,
            "matched_in_description": matched_in_description,
            "match_score": highest_match_score,
        }
        logger.info(f"Item {product_id} processed successfully.")
        return processed_item

    except Exception as e:
        item_id_str = item.get("id", "UNKNOWN_ID")
        logger.exception(f"Critical error processing item {item_id_str}: {e}")
        return None


def check_wallapop(
    product_name: str,
    keywords: Optional[List[str]] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    excluded_keywords: Optional[List[str]] = None,
    max_total_items: int = 100,
    order_by: str = "newest",
    time_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Main function to search Wallapop and return a list of items matching the criteria.

    Orchestrates URL setup, API fetching, item processing, and filtering.

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

    Returns:
        A list of dictionaries, where each dictionary represents a valid product
        found on Wallapop matching the criteria. Returns an empty list if no
        matches are found.

    Raises:
        WallaPyConfigurationError: If input parameters like price range are invalid.
        WallaPyRequestError: If API requests fail after retries.
        WallaPyParsingError: If the API response cannot be parsed.
        WallaPyException: For other unexpected errors during the process.
    """
    logger.info(f"Starting Wallapop check for '{product_name}'")
    logger.debug(
        f"Parameters: keywords={keywords}, price=({min_price}-{max_price}), excluded={excluded_keywords}, max_items={max_total_items}, order={order_by}, time={time_filter}"
    )

    # --- Input Validation and Cleaning ---
    try:
        validate_prices(min_price, max_price)
    except WallaPyConfigurationError as e:  # Usa l'eccezione corretta
        logger.error(f"Invalid configuration: {e}")
        raise

    excluded_keywords = excluded_keywords or []
    keywords = keywords or []

    keywords_cleaned = [clean_text(kw) for kw in keywords if clean_text(kw)]
    excluded_keywords_cleaned = [
        clean_text(term) for term in excluded_keywords if clean_text(term)
    ]

    if not product_name:
        error_msg = "Product name cannot be empty"
        logger.error(error_msg)

    # --- Setup URL ---
    try:
        initial_url = setup_url(
            product_name=product_name,
            min_price=min_price,
            max_price=max_price,
            order_by=order_by,
            time_filter=time_filter,
        )
    except WallaPyConfigurationError as e:  # Usa l'eccezione corretta
        error_msg = f"Configuration error setting up URL: {e}"
        logger.error(error_msg)
        raise  # Rilancia l'eccezione specifica
    except Exception as e:
        error_msg = f"Unexpected error setting up URL: {e}"
        logger.exception(error_msg)
        raise WallaPyException(error_msg) from e  # Incapsula in eccezione generica

    # --- Fetch Raw Data ---
    raw_items_data = []  # Inizializza per evitare UnboundLocalError
    try:
        raw_items_data = fetch_wallapop_items(initial_url, HEADERS, max_total_items)
    except (
        WallaPyRequestError
    ) as e:  # Cattura eccezioni specifiche se fetch_wallapop_items le lancia
        error_msg = f"Failed to fetch items from Wallapop: {e}"
        logger.error(error_msg)
        raise  # Rilancia l'eccezione specifica
    except WallaPyParsingError as e:
        error_msg = f"Failed to parse Wallapop response: {e}"
        logger.error(error_msg)
        raise  # Rilancia l'eccezione specifica
    except Exception as e:
        error_msg = f"Unexpected error fetching items: {e}"
        logger.exception(error_msg)
        raise WallaPyException(error_msg) from e  # Incapsula in eccezione generica

    if not raw_items_data:
        logger.info(
            f"No raw items found for '{product_name}' on Wallapop matching initial API query."
        )
        return []
    # --- Process and Filter Items ---
    valid_products = []
    processed_ids = set()

    for item in raw_items_data:
        item_id = item.get("id")
        if not item_id or item_id in processed_ids:
            logger.debug(f"Skipping item with duplicate or missing ID: {item_id}")
            continue

        try:
            processed_product = process_wallapop_item(
                item=item,
                search_product_name=product_name,
                search_keywords=keywords_cleaned,
                min_price=min_price,
                max_price=max_price,
                excluded_keywords=excluded_keywords_cleaned,
            )

            if processed_product:
                valid_products.append(processed_product)
                processed_ids.add(item_id)
        except Exception as e:
            item_id_str = item.get("id", "UNKNOWN_ID")
            logger.error(f"Error processing item {item_id_str}: {e}", exc_info=True)

    logger.info(
        f"Processing complete. Found {len(valid_products)} valid products matching all criteria."
    )
    return valid_products
