"""
Seed the master_products catalog from Open Food Facts API.

Usage:
  python seed_catalog.py                    # default: veterinary/pet products
  python seed_catalog.py --query "alimento mascota" --pages 5
  python seed_catalog.py --categories       # seed common vet product categories

Open Food Facts API: https://wiki.openfoodfacts.org/API
"""
import argparse
import sys
import time

import requests
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.database import SessionLocal
from models.master_product import MasterProduct

OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

# Categories relevant to veterinary clinics
VET_QUERIES = [
    "alimento perro",
    "alimento gato",
    "dog food",
    "cat food",
    "pet food",
    "veterinary",
    "antiparasitario",
    "shampoo mascota",
    "suplemento mascota",
]


def fetch_off_page(query: str, page: int = 1, page_size: int = 100) -> list[dict]:
    """Fetch one page from Open Food Facts search API."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": page_size,
        "fields": "code,product_name,brands,categories,image_url",
    }
    headers = {"User-Agent": "VetCoreSoft-CatalogSeeder/1.0"}
    resp = requests.get(OFF_SEARCH_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("products", [])


def seed_from_off(query: str, max_pages: int = 3):
    """Fetch products from Open Food Facts and upsert into master_products."""
    db = SessionLocal()
    total_inserted = 0
    total_updated = 0

    for page in range(1, max_pages + 1):
        print(f"  [{query}] page {page}/{max_pages}...", end=" ", flush=True)
        try:
            products = fetch_off_page(query, page=page)
        except Exception as e:
            print(f"ERROR: {e}")
            break

        if not products:
            print("no more results")
            break

        for p in products:
            ean = (p.get("code") or "").strip()
            name = (p.get("product_name") or "").strip()
            if not ean or not name or len(ean) < 4:
                continue

            stmt = pg_insert(MasterProduct).values(
                ean=ean,
                description=name[:300],
                brand=(p.get("brands") or "")[:150] or None,
                category=(p.get("categories") or "")[:100] or None,
                image_url=p.get("image_url") or None,
                source="openfoodfacts",
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["ean"],
                set_={
                    "description": stmt.excluded.description,
                    "brand": stmt.excluded.brand,
                    "category": stmt.excluded.category,
                    "image_url": stmt.excluded.image_url,
                    "source": stmt.excluded.source,
                },
            )
            result = db.execute(stmt)
            if result.rowcount:
                total_inserted += 1

        db.commit()
        print(f"{len(products)} fetched")
        time.sleep(1)  # rate-limit courtesy

    db.close()
    return total_inserted


def main():
    parser = argparse.ArgumentParser(description="Seed catalog from Open Food Facts")
    parser.add_argument("--query", type=str, help="Custom search query")
    parser.add_argument("--pages", type=int, default=3, help="Pages per query (default: 3)")
    parser.add_argument("--categories", action="store_true", help="Seed all vet categories")
    args = parser.parse_args()

    queries = []
    if args.query:
        queries = [args.query]
    elif args.categories:
        queries = VET_QUERIES
    else:
        queries = VET_QUERIES

    total = 0
    for q in queries:
        print(f"\nSeeding: '{q}'")
        count = seed_from_off(q, max_pages=args.pages)
        total += count

    print(f"\n✅ Done. Total products upserted: {total}")

    # Show stats
    db = SessionLocal()
    count = db.query(MasterProduct).count()
    db.close()
    print(f"📦 Catalog size: {count} products")


if __name__ == "__main__":
    main()
