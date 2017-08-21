import pytest
from aiossdb import SSDBConnectionPool, SSDBConnection


def _assert_defaults(pool):
    assert isinstance(pool, SSDBConnectionPool)
    assert pool.minsize == 1
    assert pool.maxsize == 10
    assert pool.size == 1
    assert pool.freesize == 1
    assert pool._waiter is None


@pytest.mark.asyncio
async def test_connect_pool(pool):
    _assert_defaults(pool)


@pytest.mark.asyncio
async def test_get_connection(pool):
    conn, address = await pool.get_connection()

    assert isinstance(conn, SSDBConnection)
    assert not conn.closed
    assert conn.address == address
    assert pool.freesize == 0

    # 会直接放入可用连接池
    await pool.release(conn)

    assert pool.freesize == 0
    assert pool.size == 0
