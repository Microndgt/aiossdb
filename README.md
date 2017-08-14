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

- Connection

```
import asyncio
from aiossdb import create_connection, ReplyError


loop = asyncio.get_event_loop()


@asyncio.coroutine
def connect_tcp():
    conn = yield from create_connection(('localhost', 8888), encoding='utf-8')
    try:
        val = yield from conn.auth('f')
    except ReplyError as e:
        print(e)
    else:
        print(val)
        yield from conn.execute('set', 'a', 2)
        val = yield from conn.execute('hget', 'hash_name', 'hash_key')
        print(val)

    conn.close()

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