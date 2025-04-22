from wallapy import check_wallapop
import time

# Define search parameters
product_name = "ps5"
keywords = ["console", "playstation", "ps5", "playstation 5"]
min_price = 100
max_price = 200
max_items_to_fetch = 100  # Limit the number of ads to retrieve
# order_by = "price_low_to_high"  # Sort by price ascending
time_filter = "today"  # Filter for ads posted today


def main():
    """Main async function to run the check."""

    # Measure execution time
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Search operation took {elapsed_time:.2f} seconds.")

    # Print the found results
    if results:
        print(f"\nFound {len(results)} matching ads:")
        for ad in results:
            print("-" * 60)
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
            # ---
            user_info = ad.get("user_info", {})
            register_date_str = (
                user_info.get("register_date").strftime("%Y-%m-%d %H:%M")
                if user_info.get("register_date")
                else "N/A"
            )

            print(f"Username: {user_info.get('username', 'N/A')}")
            print(f"User link : {user_info.get('link', 'N/A')}")
            print(f"User register date: {register_date_str}")
    else:
        print("\nNo ads found matching the specified criteria.")


if __name__ == "__main__":
    main()
