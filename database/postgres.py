from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB


def get_postgres_db_url_async():
    return "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(POSTGRES_USER, POSTGRES_PASSWORD,
                                                             POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB)


engine_async = create_async_engine(get_postgres_db_url_async(), pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine_async, class_=AsyncSession, autoflush=False, expire_on_commit=False)
