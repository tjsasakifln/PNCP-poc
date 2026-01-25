"""
Example demonstrating automatic pagination with fetch_all().

This script shows how to use the new pagination features to fetch
all procurement records across multiple pages.
"""

import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, "..")

from pncp_client import PNCPClient

# Configure logging to see pagination progress
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s"
)


def example_basic_pagination():
    """Example 1: Basic pagination for a single UF."""
    print("\n=== Example 1: Basic Pagination (Single UF) ===\n")

    client = PNCPClient()

    # Fetch all records for São Paulo in January 2025
    bids = []
    for bid in client.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31", ufs=["SP"]
    ):
        bids.append(bid)

    print(f"Total bids fetched: {len(bids)}")
    if bids:
        print(f"First bid: {bids[0].get('codigoCompra', 'N/A')}")
        print(f"Last bid: {bids[-1].get('codigoCompra', 'N/A')}")

    client.close()


def example_multiple_ufs():
    """Example 2: Pagination across multiple UFs."""
    print("\n=== Example 2: Multiple UFs ===\n")

    client = PNCPClient()

    # Fetch records for SP, RJ, and MG
    bids_by_uf = {}

    for bid in client.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31", ufs=["SP", "RJ", "MG"]
    ):
        uf = bid.get("uf", "UNKNOWN")
        bids_by_uf[uf] = bids_by_uf.get(uf, 0) + 1

    print("\nBids by UF:")
    for uf, count in sorted(bids_by_uf.items()):
        print(f"  {uf}: {count} bids")

    client.close()


def example_with_progress_callback():
    """Example 3: Using progress callback to track pagination."""
    print("\n=== Example 3: Progress Callback ===\n")

    def show_progress(page, total_pages, items_fetched):
        """Progress callback to show pagination status."""
        print(f"Progress: Page {page}/{total_pages} - {items_fetched} items fetched")

    client = PNCPClient()

    bids = list(
        client.fetch_all(
            data_inicial="2025-01-01",
            data_final="2025-01-07",  # Shorter range
            ufs=["SP"],
            on_progress=show_progress,
        )
    )

    print(f"\nFinal total: {len(bids)} bids")

    client.close()


def example_generator_usage():
    """Example 4: Using generator pattern for memory efficiency."""
    print("\n=== Example 4: Memory-Efficient Generator ===\n")

    client = PNCPClient()

    # Process records one at a time without loading all into memory
    count = 0
    high_value_count = 0

    for bid in client.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31", ufs=["SP"]
    ):
        count += 1

        # Process each bid immediately
        valor = bid.get("valorTotalEstimado", 0)
        if valor and valor > 1_000_000:
            high_value_count += 1

        # Example: Stop early if we found enough
        if high_value_count >= 10:
            print(f"Found {high_value_count} high-value bids, stopping early")
            break

    print(f"Processed {count} bids")
    print(f"High-value bids (>R$ 1M): {high_value_count}")

    client.close()


if __name__ == "__main__":
    print("=" * 70)
    print("PNCP Client - Automatic Pagination Examples")
    print("=" * 70)

    # Run examples
    example_basic_pagination()
    example_multiple_ufs()
    example_with_progress_callback()
    example_generator_usage()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
