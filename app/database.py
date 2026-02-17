
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

#  Create async database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Log all SQL queries (helpful for learning/debugging)
    future=True
)

#  Session factory for database transactions
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False  # Don't expire objects after commit
)

#  Base class for all database models
class Base(DeclarativeBase):
    pass

#  Dependency function to get database session
async def get_async_session():
    async with async_session_maker() as session:
        yield session