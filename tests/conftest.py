import pytest
import asyncio
import aiossdb


# hooks

@pytest.mark.tryfirst
def pytest_pyfunc_call(pyfuncitem):
    """如果pyfuncitem.obj是一个asyncio协程的化，通过事件循环执行而不是直接调用"""
    print(pyfuncitem)
    if "run_loop" in pyfuncitem.keywords:
        funcargs = pyfuncitem.funcargs
        loop = funcargs["loop"]
        testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}
        fut = asyncio.ensure_future(pyfuncitem.obj(**testargs), loop=loop)
        loop.run_until_complete(fut)
        return True


@pytest.mark.tryfirst
def pytest_pycollect_makeitem(collector, name, obj):
    if collector.funcnamefilter(name):
        if not callable(obj):
            return
        item = pytest.Function(name, parent=collector)
        if 'run_loop' in item.keywords:
            # 将asyncio的协程作为普通的函数，而不是生成器
            return list(collector._genfunctions(name, obj))


@pytest.fixture
def local_server():
    return '127.0.0.1', 8888


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture
def create_connection(loop):

    conns = []

    @asyncio.coroutine
    def f(*args, **kwargs):
        kwargs.setdefault('loop', loop)
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
            loop.run_until_complete(asyncio.gather(*waiters, loop=loop))

