import pytest
from aiossdb import SSDBConnectionPool, SSDBConnection, ReplyError, PoolClosedError


def _assert_defaults(pool):
    assert isinstance(pool, SSDBConnectionPool)
    assert pool.minsize == 1
    assert pool.maxsize == 10
    assert pool.size == 1
    assert pool.freesize == 1
    assert pool._waiter is None
    assert str(pool) == '<SSDBConnectionPool [size:[1:10], free:1]>'


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

    assert pool.freesize == 1
    assert pool.size == 1


@pytest.mark.asyncio
async def test_execute_commands(pool):
    await pool.auth('')
    await pool.execute('set', 'a', 1)

    res = await pool.execute('get', 'a')

    assert res[0] == '1'

    await pool.execute('del', 'a')

    with pytest.raises(ReplyError):
        await pool.execute('get', 'a')

    await pool.execute('hset', 'hname', 'hkey', 1)

    res = await pool.execute('hget', 'hname', 'hkey')

    assert res[0] == '1'

    await pool.execute('hclear', 'hname')

    with pytest.raises(ReplyError):
        await pool.execute('hget', 'hname', 'hkey')


@pytest.mark.asyncio
async def test_more_connections(pool):
    conn1, address1 = await pool.get_connection()
    conn2, address2 = await pool.get_connection()

    assert pool.freesize == 0
    assert pool.size == 2

    await pool.release(conn1)

    assert pool.freesize == 1
    assert pool.size == 2

    await pool.release(conn2)

    assert pool.freesize == 2
    assert pool.size == 2

    conn1.close()
    await conn1.wait_closed()

    pool._drop_closed()

    assert pool.freesize == 1
    assert pool.size == 1

    pool.close()
    await pool.wait_closed()

    assert pool.closed

    with pytest.raises(PoolClosedError):
        await pool.release(conn2)


@pytest.mark.asyncio
async def test_close_pool(pool):

    conn, addr = await pool.get_connection()
    await pool.release(conn)
    assert pool.freesize == 1
    assert pool.size == 1

    conn.close()
    await conn.wait_closed()

    conn, addr = await pool.get_connection()
    assert pool.freesize == 0
    assert pool.size == 1

    pool.close()
    await pool.wait_closed()

    assert pool.closed

    with pytest.raises(PoolClosedError):
        await pool.new_connection()