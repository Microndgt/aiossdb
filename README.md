# aiossdb
aiossdb is a library for accessing a ssdb database from the asyncio

Requirements
============

- Python_ 3.5+

DO and TODO
===========

- [x] base async ssdb connection
- [x] ssdb parser
- [] ssdb async connection pool


Quick Start
===========

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
        val = yield from conn.execute('hget', 'tdx_year_rank', 'f003006001000055')
        print(val)

    conn.close()

loop.run_until_complete(connect_tcp())
loop.close()
```

Exceptions
==========

- SSDBError
    - ConnectionClosedError
    - ReplyError
    - ProtocolError