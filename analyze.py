import asyncio
import time
from sqlalchemy import select, func
from backend.database import AsyncSessionLocal
from backend.models import SignalRejection

async def analyze():
    now = int(time.time())
    async with AsyncSessionLocal() as session:
        stmt = select(SignalRejection.reject_reason, func.count(SignalRejection.id)).where(SignalRejection.rejected_at > now - 600).group_by(SignalRejection.reject_reason)
        res = await session.execute(stmt)
        rows = res.all()
        print("Rejection Reasons (last 10 min):")
        for r in rows:
            print(f"{r[1]} x {r[0]}")

if __name__ == "__main__":
    asyncio.run(analyze())
