"""
Core logic for searching and processing Wallapop items.

Provides functions to orchestrate the search based on criteria,
process individual items, and filter them according to requirements.
"""

import datetime
import logging
from typing import List, Dict, Any, Optional
import json  # Import json module
import asyncio
import httpx  # Add httpx import

from bs4 import BeautifulSoup  # Add BeautifulSoup import
from fuzzywuzzy import fuzz

# --- Use relative imports for modules within the same package ---
from . import config  # Import the whole module to access defaults
from .exceptions import (
    WallaPyConfigurationError,
    WallaPyException,
    WallaPyRequestError,
)
from .fetch_api import fetch_wallapop_items, setup_url
from .fetch_api import fetch_user_info_async  # Import async version
from .utils import clean_text, contains_excluded_terms, make_link, validate_prices, tmz

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


class WallaPyClient:
    """
    Client class for interacting with Wallapop search functionalities.

    Allows customization of search parameters like location, headers, and delays.
    """

    def __init__(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        fuzzy_thresholds: Optional[Dict[str, int]] = None,
        delay_between_requests: Optional[int] = None,
        base_url: Optional[str] = None,
        translate: Optional[bool] = None,
    ):
        """
        Initializes the WallaPyClient with custom or default configurations.

        Args:
            latitude: Latitude for location-based searches. Defaults to config.LATITUDE.
            longitude: Longitude for location-based searches. Defaults to config.LONGITUDE.
            headers: HTTP headers for API requests. Defaults to config.HEADERS.
            fuzzy_thresholds: Thresholds for fuzzy matching. Defaults to config.FUZZY_THRESHOLDS.
            delay_between_requests: Delay in milliseconds between API requests. Defaults to config.DELAY_BETWEEN_REQUESTS.
            base_url: Base URL for the Wallapop API. Defaults to config.BASE_URL_WALLAPOP.
        """
        self.latitude = latitude if latitude is not None else config.LATITUDE
        self.longitude = longitude if longitude is not None else config.LONGITUDE
        self.headers = headers if headers is not None else config.HEADERS
        self.fuzzy_thresholds = (
            fuzzy_thresholds
            if fuzzy_thresholds is not None
            else config.FUZZY_THRESHOLDS
        )
        self.delay_between_requests = (
            delay_between_requests
            if delay_between_requests is not None
            else config.DELAY_BETWEEN_REQUESTS
        )
        self.base_url = base_url if base_url is not None else config.BASE_URL_WALLAPOP
        self.translate = translate if translate is not None else config.TRANSLATE

    def _process_wallapop_item(
        self,
        item: Dict[str, Any],
        search_product_name: str,
        search_keywords: List[str],
        min_price: Optional[float],
        max_price: Optional[float],
        excluded_keywords: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Processes a single raw item dictionary from the Wallapop API.
        (Internal instance method)
        Uses fuzzy thresholds from the client instance.
        """

        try:
            product_id = item.get("id")
            if not product_id:
                logger.debug("Skipping item due to missing ID.")
                return None

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
            state = location_data.get("country_code")

            is_reserved = item.get("reserved", {}).get("flag", False)
            shipping_available = item.get("shipping", {}).get("item_is_shippable", None)

            if is_reserved:
                logger.debug(f"Item {product_id} is reserved. Skipping.")
                return None

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
                logger.warning(
                    f"Item {product_id}: Missing creation/modification date."
                )

            price_in_range = True
            if min_price is not None and product_price < min_price:
                price_in_range = False
            if max_price is not None and product_price > max_price:
                price_in_range = False

            if not price_in_range:
                logger.debug(
                    f"Item {product_id}: Skipping, price {product_price} out of range ({min_price}-{max_price})."
                )
                return None

            full_text_for_exclusion = f"{product_title} {product_description}"
            if contains_excluded_terms(
                full_text_for_exclusion,
                excluded_keywords,
                self.fuzzy_thresholds["excluded"],
            ):
                logger.debug(
                    f"Item {product_id}: Skipping due to excluded keyword match."
                )
                return None

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

                    if title_score > self.fuzzy_thresholds["title"]:
                        keyword_match_found = True
                        highest_match_score = max(highest_match_score, title_score)

                    if desc_score > self.fuzzy_thresholds["description"]:
                        keyword_match_found = True
                        matched_in_description = True
                        highest_match_score = max(highest_match_score, desc_score)

                if not keyword_match_found:
                    logger.debug(
                        f"Item {product_id}: Skipping, no keyword match above threshold. Max score: {max(all_scores) if all_scores else 0}"
                    )

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

            seller_link = f"https://it.wallapop.com/user/{user_id}" if user_id else None

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
                "product_details": {},
                "characteristics": None,
                "views": None,
                "state": state,
                "brand": None,
                "model": None,
                "user_info": {},
                "shipping_available": shipping_available,
            }
            logger.info(f"Item {product_id} processed successfully.")
            return processed_item

        except Exception as e:
            item_id_str = item.get("id", "UNKNOWN_ID")
            logger.exception(f"Critical error processing item {item_id_str}: {e}")
            return None

    async def _get_details(
        self, item: Dict[str, Any], client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Fetches and parses detailed information about a Wallapop item asynchronously,
        prioritizing embedded JSON data (__NEXT_DATA__).

        Args:
            item: The dictionary representing the processed item, must contain the 'link'.
            client: An active httpx.AsyncClient instance.

            translate: Flag to indicate whether to translate the description and title.
        Returns:
            The input item dictionary updated with detailed information if found.
        """
        translate = self.translate
        item_id = item.get("id", "UNKNOWN_ID")
        url = item.get("link")

        if not url:
            logger.warning(f"Item {item_id}: Missing link, cannot fetch details.")
            return item

        logger.debug(f"Fetching details for item {item_id} from {url}")
        try:
            headers = self.headers or config.HEADERS
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")

            # --- Try extracting data from __NEXT_DATA__ JSON ---
            next_data_script = soup.find(
                "script", id="__NEXT_DATA__", type="application/json"
            )
            details_found_in_json = False

            if next_data_script:
                try:
                    next_data = json.loads(next_data_script.string)

                    item_data = (
                        next_data.get("props", {}).get("pageProps", {}).get("item", {})
                    )

                    if item_data:
                        details_found_in_json = True
                        if translate:
                            item["title"] = (
                                item_data.get("title").get("translated")
                                if item_data.get("title").get("translated") is not None
                                else item_data.get("title").get("original")
                            )
                            item["description"] = (
                                item_data.get("description").get("translated")
                                if item_data.get("description").get("translated")
                                is not None
                                else item_data.get("description").get("original")
                            )

                        item["model"] = item_data.get("model")
                        item["brand"] = item_data.get("brand")
                        item["characteristics"] = item_data.get("characteristics")
                        item["views"] = item_data.get("views")
                        item["product_details"] = item_data

                        # Fetch user info asynchronously
                        user_info = await fetch_user_info_async(
                            client=client,
                            user_id=item_data.get("userId"),
                        )

                        item["user_info"] = {
                            "userId": user_info.get("id"),
                            "username": user_info.get("micro_name"),
                            "profile_picture": user_info.get("image", {})
                            .get("urls_by_size", {})
                            .get("large"),
                            "city": user_info.get("location").get("city"),
                            "link": user_info.get("url_share"),
                            "register_date": user_info.get("register_date"),
                            "is_top_profile": user_info.get("is_top_profile"),
                        }

                        timestamp_ms = user_info.get("register_date")
                        if timestamp_ms:
                            try:
                                product_date_utc = datetime.datetime.fromtimestamp(
                                    timestamp_ms / 1000, tz=datetime.timezone.utc
                                )
                                item["user_info"]["register_date"] = product_date_utc
                            except (TypeError, ValueError):
                                logger.warning(
                                    f"User {item_id}: Invalid timestamp format ({timestamp_ms}). Cannot parse date."
                                )
                        else:
                            logger.warning(
                                f"User {item_id}: Missing creation/modification date."
                            )

                    else:
                        logger.debug(
                            f"Item {item_id}: 'item' data not found within pageProps in JSON."
                        )

                except json.JSONDecodeError:
                    logger.warning(
                        f"Item {item_id}: Failed to decode __NEXT_DATA__ JSON."
                    )
                except Exception as e:
                    logger.warning(
                        f"Item {item_id}: Error processing __NEXT_DATA__ JSON: {e}"
                    )
            else:
                logger.warning(
                    f"Item {item_id}: __NEXT_DATA__ script tag not found. Details might be missing."
                )

            if not details_found_in_json:
                logger.warning(
                    f"Item {item_id}: Could not extract detailed description or characteristics from JSON."
                )

        except httpx.RequestError as e:
            logger.error(f"Item {item_id}: Failed to fetch details from {url}: {e}")
        except Exception as e:
            logger.exception(f"Item {item_id}: Error parsing details page {url}: {e}")

        return item

    async def check_wallapop(
        self,
        product_name: str,
        keywords: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        excluded_keywords: Optional[List[str]] = None,
        max_total_items: int = 100,
        order_by: str = "newest",
        time_filter: Optional[str] = None,
        verbose: int = 0,
        deep_search: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Main async instance method to search Wallapop and return a list of items matching the criteria.

        Uses configuration (location, headers, delays) stored in the client instance.
        Orchestrates URL setup, API fetching, item processing, and filtering.
        """
        if verbose == 0:
            log_level = logging.WARNING
        elif verbose == 1:
            log_level = logging.INFO
        elif verbose >= 2:
            log_level = logging.DEBUG
        else:
            log_level = logging.WARNING

        package_logger = logging.getLogger("wallapy")
        package_logger.setLevel(log_level)
        for handler in package_logger.handlers or logging.getLogger().handlers:
            handler.setLevel(log_level)

        logger.info(
            f"Starting Wallapop check for '{product_name}' using client instance config"
        )
        logger.debug(
            f"Parameters: keywords={keywords}, price=({min_price}-{max_price}), excluded={excluded_keywords}, max_items={max_total_items}, order={order_by}, time={time_filter}, verbose={verbose}"
        )
        logger.debug(
            f"Client config: lat={self.latitude}, lon={self.longitude}, delay={self.delay_between_requests}"
        )

        try:
            validate_prices(min_price, max_price)
        except WallaPyConfigurationError as e:
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
            raise WallaPyConfigurationError(error_msg)

        try:
            initial_url = setup_url(
                product_name=product_name,
                min_price=min_price,
                max_price=max_price,
                order_by=order_by,
                time_filter=time_filter,
                latitude=self.latitude,
                longitude=self.longitude,
                base_url=self.base_url,
            )
        except WallaPyConfigurationError as e:
            error_msg = f"Configuration error setting up URL: {e}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error setting up URL: {e}"
            logger.exception(error_msg)
            raise WallaPyException(error_msg) from e

        raw_items_data = []
        try:
            raw_items_data = fetch_wallapop_items(
                initial_url,
                headers=self.headers,
                max_total_items=max_total_items,
                delay_between_requests=self.delay_between_requests,
            )
        except WallaPyRequestError as e:
            error_msg = f"Failed to fetch items from Wallapop: {e}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error fetching items: {e}"
            logger.exception(error_msg)
            raise WallaPyException(error_msg) from e

        if not raw_items_data:
            logger.info(
                f"No raw items found for '{product_name}' on Wallapop matching initial API query."
            )
            return []

        valid_products = []
        processed_ids = set()

        for item in raw_items_data:

            item_id = item.get("id")
            if not item_id or item_id in processed_ids:
                logger.debug(f"Skipping item with duplicate or missing ID: {item_id}")
                continue

            try:
                processed_product = self._process_wallapop_item(
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

        # --- Deep Search (Concurrent Detail Fetching) ---
        if deep_search and valid_products:
            logger.info(
                f"Deep search enabled. Fetching details for {len(valid_products)} items concurrently."
            )
            tasks = []
            async with httpx.AsyncClient(
                headers=self.headers, follow_redirects=True
            ) as client:
                for i, product in enumerate(valid_products):
                    tasks.append(
                        asyncio.create_task(
                            self._get_details(product, client),
                            name=f"get_details_{product.get('id', i)}",
                        )
                    )

                detailed_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Update valid_products with detailed results, handling potential errors
            valid_products = [
                res for res in detailed_results if not isinstance(res, Exception)
            ]
            # Log errors for tasks that failed
            for i, res in enumerate(detailed_results):
                if isinstance(res, Exception):
                    task_name = tasks[i].get_name()  # Requires Python 3.8+
                    logger.error(f"Error during deep search task '{task_name}': {res}")

        logger.info(
            f"Processing complete. Found {len(valid_products)} valid products matching all criteria."
        )
        return valid_products
