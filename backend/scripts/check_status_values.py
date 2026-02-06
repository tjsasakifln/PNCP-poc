#!/usr/bin/env python3
"""Quick script to check actual status values from PNCP API."""
import sys
import os
from datetime import date, timedelta
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pncp_client import PNCPClient

def main():
    client = PNCPClient()
    data_final = date.today()
    data_inicial = data_final - timedelta(days=7)

    print(f"Fetching bids from {data_inicial} to {data_final}...")

    status_values = Counter()
    count = 0

    for lic in client.fetch_all(
        data_inicial=data_inicial.isoformat(),
        data_final=data_final.isoformat()
    ):
        situacao = (
            lic.get("situacaoCompra") or
            lic.get("situacao") or
            lic.get("statusCompra") or
            "CAMPO_VAZIO"
        )
        status_values[situacao] += 1
        count += 1

        if count >= 200:  # Limite para debug
            break

    print(f"\nProcessed {count} bids")
    print(f"\nStatus values found (top 10):")
    for status, cnt in status_values.most_common(10):
        print(f"  {cnt:4d}x: '{status}'")

if __name__ == "__main__":
    main()
