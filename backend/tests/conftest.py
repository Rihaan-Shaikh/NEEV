import pytest
import pytest_asyncio
import os
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app, _rate_limits
from app.seed.seed_data import seed_all_data

# Use dedicated PostgreSQL test database ONLY
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:2006@localhost:5432/neev_test")

if "sqlite" in TEST_DB_URL.lower():
    raise RuntimeError("Test execution aborted: SQLite test database is strictly prohibited in NEEV.")
if "neev_dev" in TEST_DB_URL.lower():
    raise RuntimeError("Test execution aborted: Tests must run against an isolated test database (not development).")

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    await seed_all_data(session_factory=session_factory)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def async_client():
    # Per-test engine with NullPool attached to the current test loop
    test_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    _rate_limits.clear()
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    _rate_limits.clear()
    await test_engine.dispose()
