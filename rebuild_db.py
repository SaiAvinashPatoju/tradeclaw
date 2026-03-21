import asyncio
from sqlalchemy import text
from backend.database import engine, Base
from backend.models import *

async def drop_and_create():
    async with engine.begin() as conn:
        print("Dropping schema public cascade...")
        await conn.execute(text('DROP SCHEMA public CASCADE'))
        await conn.execute(text('CREATE SCHEMA public'))
        print("Creating all tables via SQLAlchemy metadata...")
        await conn.run_sync(Base.metadata.create_all)
    print("Done")

if __name__ == "__main__":
    asyncio.run(drop_and_create())
