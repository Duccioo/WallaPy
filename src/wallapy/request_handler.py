"""
Handles robust HTTP requests with retries, random user agents, and error handling.
Includes session management for connection pooling and retry strategies.
"""

import random
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any


# ---
from .config import LATITUDE, LONGITUDE, REQUEST_TIMEOUT, MAX_RETRIES, USER_AGENTS

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed level to INFO to see retry attempts
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)  # Use __name__ for logger name


# Configure session with automatic retries
# Increased backoff factor slightly for more delay between retries
retry_strategy = Retry(
    total=MAX_RETRIES,  # Total number of retries
    backoff_factor=1.5,  # Increased backoff factor
    status_forcelist=[429, 500, 502, 503, 504],  # Status codes to trigger retry
    allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
)

# Create a global session object
session = requests.Session()
adapter = HTTPAdapter(
    max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
)  # Increased pool size
session.mount("https://", adapter)
session.mount("http://", adapter)


def safe_request(
    url: str,
    timeout: int = REQUEST_TIMEOUT,  # Increased default timeout
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    latitude: Optional[float] = LATITUDE,
    longitude: Optional[float] = LONGITUDE,
) -> Optional[requests.Response]:
    """
    Performs an HTTP request using the pre-configured session with retries,
    random user agents, and randomized location parameters.

    Args:
        url: The URL for the request.
        timeout: Request timeout in seconds. Defaults to 15.
        method: HTTP method (e.g., "GET", "POST"). Defaults to "GET".
        data: Dictionary of data to send in the request body (for POST, PUT).
              Will be JSON encoded if provided. Defaults to None.
        params: Dictionary of URL query parameters. Defaults to None.
        headers: Dictionary of additional HTTP headers. Defaults to None.

    Returns:
        A requests.Response object on success, or None if the request fails
        after all retries configured in the session.
    """
    # Generate random coordinates (consider making location configurable)
    # Wallapop uses these to tailor results, but their exact impact varies.
    latitude = latitude + random.uniform(-0.05, 0.05)
    longitude = longitude + random.uniform(-0.05, 0.05)

    # Initialize parameters, adding location
    current_params = params or {}
    current_params.update(
        {
            "latitude": f"{latitude:.6f}",  # Format for consistency
            "longitude": f"{longitude:.6f}",
        }
    )

    # Set default headers and update with provided ones
    request_headers = {"User-Agent": random.choice(USER_AGENTS)}
    if headers:
        request_headers.update(headers)

    # We make a single request call here, and requests/urllib3 handles retries internally.
    logger.debug(f"Attempting {method} {url[:50]}...")  # Log URL, truncate if too long

    if data:
        logger.debug(f"Data: {data}")

    try:
        response = session.request(
            method=method.upper(),
            url=url,
            headers=request_headers,
            timeout=timeout,
            params=current_params,
            json=(
                data if data and method.upper() in ["POST", "PUT", "PATCH"] else None
            ),
            data=(
                data
                if data and method.upper() not in ["POST", "PUT", "PATCH"]
                else None
            ),
        )

        # raise_for_status() will raise an HTTPError for 4xx/5xx responses.
        # The Retry strategy already handles retries for specific status codes (429, 5xx).
        # If it fails after retries, raise_for_status will trigger the exception.
        response.raise_for_status()
        logger.debug(f"Request successful: {url[:50]}... [{response.status_code}]")
        return response

    except requests.exceptions.HTTPError as e:
        # This error occurs if raise_for_status is called on a bad response (4xx/5xx)
        # *after* retries (if applicable for the status code) have failed.
        status_code = e.response.status_code if e.response else "N/A"
        logger.error(f"HTTP Error after retries: {e} - Status Code: {status_code}")
        # Log response body for debugging if possible
        try:
            logger.error(f"Response body: {e.response.text[:500]}...")
        except Exception:
            logger.error("Could not read response body.")
        return None  # Indicate failure after retries

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # These errors are typically handled by the Retry strategy as well.
        # If they occur here, it means retries failed.
        logger.error(f"Connection/Timeout Error after retries: {e}")
        return None  # Indicate failure after retries

    except requests.exceptions.RequestException as e:
        # Catch other potential requests exceptions that might not be retryable
        # or occurred outside the retry scope.
        logger.error(f"An unexpected requests error occurred: {e}")
        return None

    except Exception as e:
        # Catch any other unexpected errors during the request process
        logger.exception(
            f"An unexpected error occurred during request preparation or execution for {url}: {e}"
        )
        return None
