import pytest
import asyncio
import aiossdb


# pytest-asyncio 可以定义异步的fixture和testcase，有默认的event_loop fixture
# hooks

@pytest.fixture
def local_server():
    return '127.0.0.1', 8888


@pytest.fixture
def create_connection(event_loop):

    conns = []

    @asyncio.coroutine
    def f(*args, **kwargs):
        kwargs.setdefault('loop', event_loop)
        conn = yield from aiossdb.create_connection(*args, **kwargs)
        # 这里要关闭连接，因为是协程，所以不能直接使用yield，必须使用return
        # 那么就得想个办法来处理这些连接
        conns.append(conn)
        return conn

    try:
        yield f
    finally:
        waiters = []
        while conns:
            conn = conns.pop()
            conn.close()
            waiters.append(conn.wait_closed())
        if waiters:
            event_loop.run_until_complete(asyncio.gather(*waiters, loop=event_loop))


@pytest.fixture
def create_connection_pool(event_loop):
    pools = []

    @asyncio.coroutine
    def f(*args, **kwargs):
        kwargs.setdefault('loop', event_loop)
        pool = yield from aiossdb.create_pool(*args, **kwargs)
        # 这里要关闭连接，因为是协程，所以不能直接使用yield，必须使用return
        # 那么就得想个办法来处理这些连接
        pools.append(pool)
        return pool

    try:
        yield f
    finally:
        waiters = []
        while pools:
            conn = pools.pop()
            conn.close()
            waiters.append(conn.wait_closed())
        if waiters:
            event_loop.run_until_complete(asyncio.gather(*waiters, loop=event_loop))


@pytest.fixture
def pool(create_connection_pool, event_loop, local_server):
    created_pool = event_loop.run_until_complete(create_connection_pool(local_server, loop=event_loop))
    return created_pool
