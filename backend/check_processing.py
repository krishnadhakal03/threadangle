import asyncio
from database import AsyncSessionLocal
from models import Generation
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Generation)
            .where(Generation.status == 'processing')
            .order_by(Generation.created_at.desc())
        )
        rows = result.scalars().all()
        print(f"Found {len(rows)} processing video(s):")
        for g in rows:
            print(f"  ID={g.id}  run_id={g.video_run_id}  created={g.created_at}  error={g.error_message}")

asyncio.run(main())
