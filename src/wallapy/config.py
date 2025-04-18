"""
Configuration constants for the WallaPy application.

Includes API endpoints, fuzzy matching thresholds, and default HTTP headers.
"""

# Base URL for the Wallapop search API endpoint
BASE_URL_WALLAPOP = (
    "https://api.wallapop.com/api/v3/search"  # Updated based on common usage
)

# Thresholds for fuzzy string matching (0-100 scale)
FUZZY_THRESHOLDS = {
    "title": 75,  # Minimum score for keyword match in title
    "description": 65,  # Minimum score for keyword match in description
    "excluded": 85,  # Minimum score to identify an excluded keyword
}

# Default HTTP headers for requests to Wallapop API
# These might need adjustments based on API requirements or observations
HEADERS = {
    "X-DeviceOS": "0",  # Often '0' for Web/Unknown, '1' for iOS, '2' for Android
    # "Accept-Language": "en-US,en;q=0.9,it;q=0.8",  # Example language preference
    # "Accept": "application/json, text/plain, */*",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    # User-Agent is handled dynamically in request_handler.py
}

LATITUDE = 43.318611  # Default latitude for searches (Madrid)
LONGITUDE = 11.330556  # Default longitude for searches (Madrid)

# Consider adding other configurations like timeouts, retry counts etc. here
# REQUEST_TIMEOUT = 15
# MAX_RETRIES = 3
