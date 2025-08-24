import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

from shared.db.base import Base

load_dotenv()

raw_url = os.getenv("DATABASE_URL")
if raw_url is None:
    raise RuntimeError("DATABASE_URL is not set in .env")

# ── normalise to asyncpg and handle SSL parameters ──────────────────────────────
if raw_url.startswith("postgres://"):
    async_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif raw_url.startswith("postgresql://"):
    async_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    async_url = raw_url  # assume caller already gave the +asyncpg prefix

# Parse URL to extract and remove problematic SSL parameters
parsed = urlparse(async_url)
if parsed.query:
    # Remove sslmode and channel_binding parameters that asyncpg doesn't understand
    query_params = parse_qs(parsed.query)
    # Filter out problematic parameters
    filtered_params = {k: v for k, v in query_params.items() 
                      if k not in ['sslmode', 'channel_binding']}
    
    # Reconstruct URL without problematic parameters
    if filtered_params:
        new_query = '&'.join([f"{k}={v[0]}" for k, v in filtered_params.items()])
        async_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
    else:
        async_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

# For Neon and other cloud providers, SSL is required by default with asyncpg
# TODO: set echo=False in production
engine = create_async_engine(async_url, echo=False, connect_args={"ssl": "require"})

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── helpers ───────────────────────────────────────────────────────────
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
