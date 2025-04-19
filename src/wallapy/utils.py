import pytz
import hashlib
import re
from fuzzywuzzy import fuzz
from typing import List, Any, Optional

# --- Import custom exceptions ---
from .exceptions import WallaPyConfigurationError

# Define a default timezone (e.g., Europe/Rome)
# Make sure 'pytz' is listed in requirements/setup.cfg
try:
    tmz = pytz.timezone("Europe/Rome")
except pytz.exceptions.UnknownTimeZoneError:
    tmz = pytz.utc  # Fallback to UTC if Rome is not found


def generate_unique_id(params: List[Any] = [], length: int = 10) -> str:
    """
    Generates a unique ID based on input parameters using SHA-256 hash.

    Args:
        params: A list of input parameters to include in the hash calculation.
                Can contain various data types, including functions (uses their name).
        length: The desired length of the output ID (truncated hash). Defaults to 10.

    Returns:
        A unique identifier string derived from the input parameters.
    """
    input_str = ""

    # Concatenate string representations of input data
    for param in params:
        if isinstance(param, list):
            # Convert list elements to string, using function names if callable
            param_str = [str(p) if not callable(p) else p.__name__ for p in param]
            input_str += "".join(param_str)  # Join list elements into a single string
        elif callable(param):
            input_str += param.__name__  # Use function name
        else:
            input_str += str(param)  # Convert other types to string

    # Calculate SHA-256 hash of the concatenated string
    hash_obj = hashlib.sha256(input_str.encode("utf-8"))  # Ensure consistent encoding
    hex_dig = hash_obj.hexdigest()

    # Return the first 'length' characters of the hash
    return hex_dig[:length]


def validate_prices(min_price: Optional[float], max_price: Optional[float]) -> None:
    """
    Validates the min and max price filters.
    Raises WallaPyConfigurationError if invalid.
    """
    if min_price is not None and min_price < 0:
        raise WallaPyConfigurationError("Minimum price cannot be negative.")
    if max_price is not None and max_price < 0:
        raise WallaPyConfigurationError("Maximum price cannot be negative.")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise WallaPyConfigurationError(
            "Minimum price cannot be greater than maximum price."
        )


def clean_text(text: Optional[str]) -> str:
    """
    Cleans text by converting to lowercase, removing extra whitespace,
    and potentially other non-alphanumeric characters (adjust as needed).
    """
    if not text:
        return ""  # Return empty string for None or empty input
    text = text.lower()
    # Remove punctuation and extra spaces (example, customize as needed)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_excluded_terms(
    text: str, excluded_keywords: List[str], threshold: int
) -> bool:
    """
    Checks if the text contains any excluded keywords using fuzzy matching.
    """
    if not excluded_keywords:
        return False  # No keywords to exclude
    text_cleaned = clean_text(text)
    for keyword in excluded_keywords:
        # Use partial_ratio for potentially finding keywords within longer strings
        if fuzz.partial_ratio(clean_text(keyword), text_cleaned) > threshold:
            return True
    return False


def make_link(web_slug: Optional[str]) -> Optional[str]:
    """
    Creates a full Wallapop item URL from its web_slug.
    """
    if not web_slug:
        return None
    # Assuming the base URL structure for items
    return f"https://wallapop.com/item/{web_slug}"
