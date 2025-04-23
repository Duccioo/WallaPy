# WallaPy 🐍

WallaPy is a Python library designed to interact with Wallapop's (unofficial) API to search for items based on various criteria. It allows automating product searches, applying filters, and retrieving detailed information about listings. The core of the library is **asynchronous** for efficiency, but a simple synchronous wrapper is provided for ease of use in synchronous code.

Developed by [duccioo](https://github.com/duccioo) ✨

## Features 🚀

*   **Advanced Search:** Search for items on Wallapop by product name and additional keywords.
*   **Multiple Filters:**
    *   Filter by price range (minimum and maximum). 💰
    *   Filter by publication period (`today`, `lastWeek`, `lastMonth` ) 📅
    *   Exclude listings containing specific keywords (supports fuzzy matching). 🚫
*   **Sorting:** Sort results by newest (`newest`), price ascending (`price_low_to_high`), or price descending (`price_high_to_low`). 📊
*   **Pagination Handling:** Automatically retrieves multiple pages of results up to a specified limit. 📄
*   **Robustness:** Handles HTTP errors, implements retry mechanisms, and rotates User-Agents for API requests. 💪
*   **Flexible Matching:** Uses fuzzy matching (via `fuzzywuzzy`) to identify relevant keywords in titles and descriptions, even with slight variations. 🔍
*   **Data Processing:** Cleans and formats data retrieved from the API into a structured format. 🧹
*   **Deep Search:** Optionally fetches detailed item information (like user details, characteristics, views) concurrently for matched items. 🕵️
*   **Error Handling:** Uses custom exceptions for better handling of library-specific errors.

## Installation 🛠️

**Using pip (Recommended):**

The easiest way to install WallaPy is directly from PyPI:

```bash
pip install wallapy
```

**From Source (for development):**

If you want to contribute or install the latest development version, you can install from source. Using a virtual environment is recommended.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/duccioo/WallaPy.git
    cd WallaPy
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```
3.  **Install the library:**
    The `pyproject.toml` file defines the dependencies. Use pip to install the library and its dependencies:
    ```bash
    pip install .
    ```
    Or, to install in editable mode:
    ```bash
    pip install -e .
    ```
    *(Note: `python-Levenshtein` is included in the dependencies and improves `fuzzywuzzy` performance)*

## Usage Example 💡

WallaPy provides a simple synchronous function `check_wallapop` for basic usage. This function handles the asynchronous operations internally.

```python
from wallapy import check_wallapop # Import the synchronous wrapper

# Execute the search
results = check_wallapop(
    product_name="iPhone 15",
    keywords=["iphone", "15", "pro", "128gb", "unlocked"],
    min_price=500,
    max_price=800,  # Set the maximum price
    excluded_keywords=["broken", "repair", "cracked screen", "rotto", "riparare"],
    max_total_items=50,  # Limit the number of listings to retrieve
    order_by="price_low_to_high", # Sort by price
)

# Print the found results
if results:
    print(f"\nFound {len(results)} matching listings:")
    for ad in results:
        print("-" * 20)
        print(f"Title: {ad['title']}")
        print(f"Price: {ad['price']} {ad.get('currency', '')}")
        print(f"Location: {ad.get('location', 'N/A')}")
        print(f"Link: {ad['link']}")
else:
    print("\nNo listings found matching the specified criteria.")
```

**Note:** For integration into existing `asyncio` applications, it's recommended to instantiate `WallaPyClient` directly and use its `async check_wallapop(...)` method to avoid potential issues with `asyncio.run()` within a running event loop. See the example in `src/test/test.py` for asynchronous usage.

## Project Structure (`src/wallapy`) 📁

*   `pyproject.toml`: (In the root) Main configuration file for the package build and dependencies.
*   `__init__.py`: Makes the `wallapy` directory a Python package and exposes the public interface (the `WallaPyClient` class, the synchronous `check_wallapop` wrapper, and exceptions).
*   `check.py`: Contains the `WallaPyClient` class with the main async logic (`check_wallapop`) for orchestrating the search and processing (`_process_wallapop_item`, `_get_details`).
*   `fetch_api.py`: Handles URL construction (`setup_url`), synchronous API data retrieval (`fetch_wallapop_items`), and asynchronous user info fetching (`fetch_user_info_async`).
*   `request_handler.py`: Provides `safe_request` (sync) and `safe_request_async` (async) functions for robust HTTP requests with retries and error handling.
*   `utils.py`: Contains utility functions for text cleaning (`clean_text`), checking excluded terms (`contains_excluded_terms`), link generation (`make_link`), price validation (`validate_prices`), etc.
*   `config.py`: Stores configuration constants like the base API URL, fuzzy matching thresholds, and default HTTP headers.
*   `exceptions.py`: Defines custom exceptions used by the library (e.g., `WallaPyRequestError`).

## TODO

- [ ] Aggiungere altri esempi di utilizzo con il client
- [ ] Inserire lo scraping via web in caso di errore API
- [ ] Migliorare il matching delle parole
- [ ] Prendere N elementi che rispettano le richieste no matter what invece di fare il fetching di N elementi e poi controllare se rispettano o meno le richieste.


## License 📜

This project is released under the Apache License 2.0. See the [LICENSE](LICENSE) file for more details.

## Disclaimer ⚠️

This tool uses unofficial Wallapop APIs. Use it at your own risk. Changes to the API by Wallapop may break the tool without notice. Respect Wallapop's terms of service. This tool is intended for personal, non-commercial use.
