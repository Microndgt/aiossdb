import pytest
import asyncio
from aiossdb import SSDBConnection, ProtocolError, ConnectionClosedError

from unittest.mock import patch


@pytest.mark.asyncio
async def test_connect_tcp(create_connection, event_loop, local_server):
    """测试连接"""
    address = local_server
    conn = await create_connection(address, loop=event_loop)
    assert isinstance(conn.address, tuple)
    assert conn.address[0] == "127.0.0.1"
    assert conn.address[1] == 8888
    assert str(conn) == "<SSDBConnection [host:{}-port:{}]>".format(address[0], address[1])

    conn = await create_connection([address[0], address[1]], loop=event_loop)
    assert isinstance(conn.address, tuple)
    assert conn.address[0] in (address[0], '::1')
    assert conn.address[1] == address[1]
    assert str(conn) == "<SSDBConnection [host:{}-port:{}]>".format(address[0], address[1])


@pytest.mark.asyncio
async def test_connect_inject_connection_cls(create_connection, event_loop, local_server):
    """测试SSDBConnection子类"""
    address = local_server

    class MyConnection(SSDBConnection):
        pass

    conn = await create_connection(address, loop=event_loop, connect_cls=MyConnection)

    assert isinstance(conn, MyConnection)


@pytest.mark.asyncio
async def test_connect_inject_connection_cls_invalid(create_connection, event_loop, local_server):
    """测试无效的connect_cls，type不能处理所给的参数，所以是TypeError"""
    address = local_server
    with pytest.raises(TypeError):
        await create_connection(address, loop=event_loop, connect_cls=type)


@pytest.mark.asyncio
async def test_connect_tcp_timeout(create_connection, event_loop, local_server):
    """测试超时是否有效"""
    address = local_server
    with patch('aiossdb.connection.asyncio.open_connection') as open_conn_mock:
        # 在open_connection之后调用，sleep 0.2s
        open_conn_mock.side_effect = lambda *a, **kw: asyncio.sleep(0.2, loop=event_loop)
        with pytest.raises(asyncio.TimeoutError):
            await create_connection(address, loop=event_loop, timeout=0.1)


def test_global_loop(create_connection, event_loop, local_server):
    """测试 SSDBConnection中的loop是否和全局loop一致"""
    address = local_server
    asyncio.set_event_loop(event_loop)

    conn = event_loop.run_until_complete(create_connection(address))
    assert conn._loop is event_loop


@pytest.mark.asyncio
async def test_protocol_error(create_connection, event_loop, local_server):
    """测试给定无效数据，引发ProtocolError"""
    address = local_server
    conn = await create_connection(address, loop=event_loop)

    reader = conn._reader

    with pytest.raises(ProtocolError):
        reader.feed_data(b'not good redis protocol response')
        await conn.execute('get', 'a')

    assert len(conn._waiters) == 0


def test_close_connection_tcp(create_connection, event_loop, local_server):
    """测试关闭连接"""
    address = local_server
    conn = event_loop.run_until_complete(create_connection(address, loop=event_loop))
    conn.close()
    with pytest.raises(ConnectionClosedError):
        event_loop.run_until_complete(conn.execute('get', 'a'))

    conn = event_loop.run_until_complete(create_connection(address, loop=event_loop))
    conn.close()
    fut = None
    with pytest.raises(ConnectionClosedError):
        fut = conn.execute('get', 'a')
    assert fut is None

    conn = event_loop.run_until_complete(create_connection(address, loop=event_loop))
    conn.close()
    with pytest.raises(ConnectionClosedError):
        conn.auth('')
