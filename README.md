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
- [x] async ssdb parser
- [x] async ssdb connection pool
- [ ] easy using ssdb async client
- [x] tests
- [ ] detailed docs
- [ ] suppress ReplyError as a choice
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
    yield from pool.release(conn)

    pool.close()
    yield form pool.wait_closed()

loop.run_until_complete(connect_tcp())
loop.close()
```

如果获取不存在的键等情况会引发`ReplyError`, 错误类型可能有: `not_found`, `error`, `fail`, `client_error`

```
try:
    val = yield from conn.execute('hget', 'hash_name', 'hash_key')
except ReplyError as e:
    print("错误类型是: {}".format(e.etype))
    print("执行的命令是: {}".format(e.command))
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

Contributor
===========

Kevin Du
--------

- Email: `dgt_x@foxmail.com`
- Site: `http://skyrover.me`