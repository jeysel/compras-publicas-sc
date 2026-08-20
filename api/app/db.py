from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import settings

pool = AsyncConnectionPool(conninfo=settings.dsn, open=False)


async def open_pool() -> None:
    await pool.open(wait=True)


async def close_pool() -> None:
    await pool.close()


@asynccontextmanager
async def get_connection() -> AsyncIterator[AsyncConnection]:
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        yield conn
