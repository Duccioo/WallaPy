# Esempio: run_check.py (nella root del progetto)
import logging
from wallapy import check_wallapop  # Importa dal pacchetto

# Configura il logging per l'applicazione
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Define search parameters
product_name = "ps5"
keywords = ["console", "playstation", "ps5", "playstation 5"]
min_price = 100
max_price = 200
max_items_to_fetch = 10  # Limit the number of ads to retrieve
# order_by = "price_low_to_high"  # Sort by price ascending
time_filter = "lastWeek"

# Execute the search
try:
    results = check_wallapop(
        product_name=product_name,
        keywords=keywords,
        min_price=min_price,
        max_price=max_price,
        max_total_items=max_items_to_fetch,
        time_filter=time_filter,
    )

    # Print the found results
    if results:
        print(f"\nFound {len(results)} matching ads:")
        for ad in results:
            print("-" * 20)
            print(f"Title: {ad['title']}")
            print(f"Price: {ad['price']} {ad.get('currency', '')}")
            # Format date nicely if available
            date_str = (
                ad["creation_date_local"].strftime("%Y-%m-%d %H:%M")
                if ad.get("creation_date_local")
                else "N/A"
            )
            print(f"Date: {date_str}")
            print(f"Location: {ad.get('location', 'N/A')}")
            print(f"Link: {ad['link']}")
            print(f"Score: {ad.get('match_score', 'N/A')}")
            print(f"Image: {ad.get('main_image', 'N/A')}")
    else:
        print("\nNo ads found matching the specified criteria.")

except ValueError as e:
    print(f"\nInput Error: {e}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    logging.exception("Error during check_wallapop execution:")
