# aiossdb
aiossdb is a library for accessing a ssdb database from the asyncio

[![Coverage Status](https://coveralls.io/repos/github/Microndgt/aiossdb/badge.svg?branch=master)](https://coveralls.io/github/Microndgt/aiossdb?branch=master)
![https://travis-ci.org/Microndgt/aiossdb.svg?branch=master](https://travis-ci.org/Microndgt/aiossdb.svg?branch=master)

Requirements
------------

- Python 3.5+

DONE and TODO
-------------

- [x] base async ssdb connection
- [x] ssdb parser
- [x] ssdb async connection pool
- [ ] easy using ssdb client
- [ ] tests
- [ ] releasing...
- [ ] and more...

Quick Start
-----------

- ConnectionPool

```
import asyncio
from aiossdb import create_pool

loop = asyncio.get_event_loop()


@asyncio.coroutine
def connect_tcp():
    pool = yield from create_pool(('localhost', 8888), loop=loop, minsize=5, maxsize=10)

    # 使用pool直接执行命令
    yield from pool.execute('set', 'a', 2)
    val = yield from pool.execute('hget', 'hash_name', 'hash_key')
    print(val)

    # 使用pool获取连接
    conn, addr = yield from pool.get_connection()
    yield from conn.execute('set', 'a', 2)
    val = yield from conn.execute('hget', 'hash_name', 'hash_key')
    print(val)
    # 获取的连接最后一定要release
    pool.release(conn)

    pool.close()
    yield form pool.wait_closed()

loop.run_until_complete(connect_tcp())
loop.close()
```

- Connection

```
import asyncio
from aiossdb import create_connection, ReplyError


loop = asyncio.get_event_loop()


@asyncio.coroutine
def connect_tcp():
    conn = yield from create_connection(('localhost', 8888), loop=loop)
    yield from conn.execute('set', 'a', 2)
    val = yield from conn.execute('hget', 'hash_name', 'hash_key')
    print(val)

    conn.close()
    yield from conn.wait_closed()

loop.run_until_complete(connect_tcp())
loop.close()
```

Exceptions
----------

- SSDBError
    - ConnectionClosedError
    - ReplyError
    - ProtocolError
    - PoolClosedError

NOTES
-----

- The preliminary test shows that `aiossdb` is 25 times fast than [pyssdb](https://github.com/ifduyue/pyssdb)