import asyncio
from .log import logger
from .errors import ReplyError


def set_result(fut, result, *info):
    if fut.done():
        logger.debug("Waiter future is already done %r %r", fut, info)
        assert fut.cancelled(), (
            "waiting future is in wrong state", fut, result, info)
    else:
        fut.set_result(result)


def set_exception(fut, exception):
    if fut.done():
        logger.debug("Waiter future is already done %r", fut)
        assert fut.cancelled(), (
            "waiting future is in wrong state", fut, exception)
    else:
        fut.set_exception(exception)


@asyncio.coroutine
def wait_ok(fut):
    yield from fut
    return True
