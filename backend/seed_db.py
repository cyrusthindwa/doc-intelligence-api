"""
Seed the database with predefined schemas.

Usage:
    python seed_db.py

Safe to run multiple times — skips existing schemas.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import AsyncSessionLocal
from services.schema_service import seed_schemas


async def main():
    print("\n🌱  Seeding database with predefined schemas...\n")

    async with AsyncSessionLocal() as db:
        result = await seed_schemas(db)

    print(f"  ✅  Inserted : {result['inserted']}")
    print(f"  ⏭   Skipped  : {result['skipped']}")
    print(f"  📊  Total    : {result['total']}")
    print("\n  Done.\n")


if __name__ == "__main__":
    asyncio.run(main())