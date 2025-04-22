"""
Configuration constants for the WallaPy application.

Includes API endpoints, fuzzy matching thresholds, and default HTTP headers.
"""

# Base URL for the Wallapop search API endpoint
BASE_URL_WALLAPOP = "https://api.wallapop.com/api/v3"  # Updated based on common usage

# Thresholds for fuzzy string matching (0-100 scale)
FUZZY_THRESHOLDS = {
    "title": 85,  # Minimum score for keyword match in title
    "description": 95,  # Minimum score for keyword match in description
    "excluded": 85,  # Minimum score to identify an excluded keyword
}

# Default HTTP headers for requests to Wallapop API
HEADERS = {
    "X-DeviceOS": "0",  # Often '0' for Web/Unknown, '1' for iOS, '2' for Android
    # "Accept-Language": "en-US,en;q=0.9,it;q=0.8",  # Example language preference
    # "Accept": "application/json, text/plain, */*",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

LATITUDE = 43.318611  # Default latitude for searches (Buonconvento)
LONGITUDE = 11.330556  # Default longitude for searches (Buonconvento)


# Expanded list of common user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 15_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/98.0.4758.85 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.101 Mobile Safari/537.36",
]

# Consider adding other configurations like timeouts, retry counts etc. here
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 500  # Delay in milliseconds between requests

TRANSLATE = True
