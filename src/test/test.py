# Esempio: run_check.py (nella root del progetto)
from wallapy import check_wallapop  # Importa il client


# Define search parameters
product_name = "ps5"
keywords = ["console", "playstation", "ps5", "playstation 5"]
min_price = 100
max_price = 200
max_items_to_fetch = 50  # Limit the number of ads to retrieve
# order_by = "price_low_to_high"  # Sort by price ascending
time_filter = "today"  # Filter for ads posted today


def main():
    """Main async function to run the check."""

    # Execute the search asynchronously
    results = check_wallapop(
        product_name=product_name,
        keywords=keywords,
        min_price=min_price,
        max_price=max_price,
        max_total_items=max_items_to_fetch,
        time_filter=time_filter,
        verbose=0,  # Aggiungi verbosità per debug se necessario
        deep_search=True,  # Abilita deep search per testare i dettagli
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
            # Stampa info utente se disponibili dal deep search
            user_info = ad.get("user_info", {})
            print(f"User ID: {user_info.get('userId', 'N/A')}")
            print(f"Username: {user_info.get('username', 'N/A')}")
            print(f"User link : {user_info.get('link', 'N/A')}")
            # print(f"Description: {ad.get('description', 'N/A')}") # Descrizione può essere lunga
    else:
        print("\nNo ads found matching the specified criteria.")


if __name__ == "__main__":
    main()
