# WallaPy 🐍

WallaPy is a Python library designed to interact with Wallapop's (unofficial) API to search for items based on various criteria. It allows automating product searches, applying filters, and retrieving detailed information about listings.

Developed by [duccioo](https://github.com/duccioo) ✨

## Features 🚀

*   **Advanced Search:** Search for items on Wallapop by product name and additional keywords.
*   **Multiple Filters:**
    *   Filter by price range (minimum and maximum). 💰
    *   Filter by publication period (`today`, `lastWeek`, `lastMonth` - *Note: API parameter needs verification*). 📅
    *   Exclude listings containing specific keywords (supports fuzzy matching). 🚫
*   **Sorting:** Sort results by newest (`newest`), price ascending (`price_low_to_high`), or price descending (`price_high_to_low`). 📊
*   **Pagination Handling:** Automatically retrieves multiple pages of results up to a specified limit. 📄
*   **Robustness:** Handles HTTP errors, implements retry mechanisms, and rotates User-Agents for API requests. 💪
*   **Flexible Matching:** Uses fuzzy matching (via `fuzzywuzzy`) to identify relevant keywords in titles and descriptions, even with slight variations. 🔍
*   **Data Processing:** Cleans and formats data retrieved from the API into a structured format. 🧹
*   **Error Handling:** Uses custom exceptions for better handling of library-specific errors.

## Installation 🛠️

Using a virtual environment is recommended.

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
    Or, to install in editable mode (useful for development):
    ```bash
    pip install -e .
    ```
    *(Note: `python-Levenshtein` is included in the dependencies and improves `fuzzywuzzy` performance)*

## Usage Example 💡

Here's a basic example of how to use the main `check_wallapop` function:

```python

from wallapy import check_wallapop

# Define search parameters
product_name = "iPhone 15"
keywords = ["pro", "128gb", "unlocked"]
min_price = 500
max_price = 800
excluded_keywords = ["broken", "repair", "cracked screen", "rotto", "riparare"]
max_items_to_fetch = 50 # Limit the number of listings to retrieve
order_by = "price_low_to_high" # Sort by price ascending

# Execute the search
results = check_wallapop(
    product_name=product_name,
    keywords=keywords,
    min_price=min_price,
    max_price=max_price,
    excluded_keywords=excluded_keywords,
    max_total_items=max_items_to_fetch,
    order_by=order_by,
)

# Print the found results
if results:
    print(f"\nFound {len(results)} matching listings:")
    for ad in results:
        print("-" * 20)
        print(f"Title: {ad['title']}")
        print(f"Price: {ad['price']} {ad.get('currency', '')}")
        # Format the date if available
        date_str = ad['creation_date_local'].strftime('%Y-%m-%d %H:%M') if ad.get('creation_date_local') else "N/A"
else:
    print("\nNo listings found matching the specified criteria.")


```

## Project Structure (`src/wallapy`) 📁

*   `pyproject.toml`: (In the root) Main configuration file for the package build and dependencies.
*   `__init__.py`: Makes the `wallapy` directory a Python package and exposes the public interface (e.g., `check_wallapop` and exceptions).
*   `check.py`: Contains the main logic (`check_wallapop`) for orchestrating the search and processing (`process_wallapop_item`).
*   `fetch_api.py`: Handles URL construction (`setup_url`) and data retrieval from the Wallapop API (`fetch_wallapop_items`), including pagination.
*   `request_handler.py`: Provides the `safe_request` function for robust HTTP requests with retries and error handling.
*   `utils.py`: Contains utility functions for text cleaning (`clean_text`), checking excluded terms (`contains_excluded_terms`), link generation (`make_link`), price validation (`validate_prices`), etc.
*   `config.py`: Stores configuration constants like the base API URL, fuzzy matching thresholds, and default HTTP headers.
*   `exceptions.py`: Defines custom exceptions used by the library (e.g., `WallaPyRequestError`).

## TODO
- [ ] Pubblicarlo su PyPI
- [ ] Aggiungere altri esempi di utilizzo
- [ ] Inserire lo scraping via web in caso di errore API
- [ ] Migliorare il matching delle parole


## License 📜

This project is released under the Apache License 2.0. See the [LICENSE](LICENSE) file for more details.

## Disclaimer ⚠️

This tool uses unofficial Wallapop APIs. Use it at your own risk. Changes to the API by Wallapop may break the tool without notice. Respect Wallapop's terms of service. This tool is intended for personal, non-commercial use.
