import pytest
from aiossdb import Client


@pytest.mark.asyncio
async def test_create_client(event_loop):
    c = Client(loop=event_loop)
    assert c._pool is None
    pool = await c.get_pool()
    assert pool is c._pool
    assert c._pool.maxsize == c.max_connection
    await c.close()
    assert c._pool is None


@pytest.mark.asyncio
async def test_execute_command(event_loop):
    c = Client(loop=event_loop)
    await c.set('a', 1)
    res = await c.get('a')
    assert res[0] == '1'
    assert c._pool is not None
    await c.close()
    assert c._pool is None
