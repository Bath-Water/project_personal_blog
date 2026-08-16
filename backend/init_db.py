"""Initialise the SQLite database: create all tables."""

import asyncio

from app.database import init_db, close_engine


async def main() -> None:
    """Entry-point when running ``python init_db.py``."""
    await init_db()
    print("Database tables created successfully.")
    await close_engine()


if __name__ == "__main__":
    asyncio.run(main())