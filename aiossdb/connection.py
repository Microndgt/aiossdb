import asyncio
import socket

from collections import deque

from .log import logger
from .parser import SSDBParser, encode_command
from .errors import ProtocolError, ReplyError, ConnectionClosedError
from .utils import wait_ok, set_result, set_exception


MAX_CHUNK_SIZE = 65536
_NOTSET = object()


@asyncio.coroutine
def create_connection(address, *, password=None, encoding=None, parser=None, loop=None,
                      timeout=None, connect_cls=None, reusable=True):
    '''
    创建SSDB数据库连接
    :param address: 类似于socket的地址，如果是tuple或者list，则应该是(host, port)这种形式，
                    但是不支持unix socket
    :param password: SSDB数据库的密码，默认是None
    :param encoding: 用于将读取的数据从bytes解码成str，默认为None
    :param parser: 根据SSDB协议解析返回数据的解析器，默认会使用自定义的SSDBParser
    :param loop:
    :param timeout: 默认情况，timeout会在连接状态下应用限制等待时间，
                    也可以使用这个参数来定义创建连接所花的时间
    :param connect_cls:
    :param reusable: 设置端口重用，默认为True
    :return: 返回一个SSDBConnection对象，如果传递了connect_cls,则会返回这个类的实例
    '''
    # 首先判断address
    assert isinstance(address, (tuple, list)), "tuple or list expected"

    # 判断timeout
    if timeout is not None and timeout <= 0:
        raise ValueError("Timeout has to be None or a number greater than 0")

    # 默认connect_cls是SSDBConnection
    # TODO: 判断传入的类是否是可以应用的连接类型
    if connect_cls is None:
        connect_cls = SSDBConnection

    # 开始连接
    host, port = address
    logger.debug("Creating tcp connection to %r", address)
    # asyncio.open_connection创建套接字连接，返回reader和writer对象，它也是一个协程
    # 实际调用的是loop.create_connection
    # wait_for函数提供等待Future或者协程完成直到超时的功能，返回协程或者Future的结果
    reader, writer = yield from asyncio.wait_for(asyncio.open_connection(host, port, loop=loop),
                                                 timeout, loop=loop)
    sock = writer.transport.get_extra_info('socket')
    if sock is not None:
        # 设置端口重用
        if reusable:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 设置TCP无延迟，其相对是 Nagle’s Algorithm
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        address = sock.getpeername()
    address = tuple(address[:2])

    conn = connect_cls(reader, writer, encoding=encoding,
                       address=address, parser=parser, loop=loop)

    try:
        if password is not None:
            yield from conn.auth(password)
    except Exception:
        conn.close()
        yield from conn.wait_closed()
        raise
    return conn


class SSDBConnection:
    def __init__(self, reader, writer, *, address, encoding=None, parser=None, loop=None):
        if loop is None:
            # 默认使用asyncio的事件循环
            loop = asyncio.get_event_loop()
        if parser is None:
            parser = SSDBParser
        assert callable(parser), "Parser argument: {} is not callable".format(parser)
        self._reader = reader
        self._writer = writer
        self._address = address
        self._loop = loop
        # 使用双端队列来记录发送的命令，在解析数据的时候popleft
        self._waiters = deque()
        # TODO: ssdb数据解析器
        self._parser = parser(encoding=encoding)
        # 创建读取的task, self._read_data()是一个协程，用来在套接字生存期间读取数据
        # ensure_future 排定协程在事件循环的执行，如果参数是Future对象，将直接返回，返回的类型是Task对象
        self._reader_task = asyncio.ensure_future(self._read_data(), loop=self._loop)
        # 创建结束期物，这个任务会等待套接字读取任务的结束（使用回调来填充期物)
        self._close_waiter = asyncio.Future(loop=self._loop)
        # 添加读取任务结束后(套接字关闭)的回调函数
        self._reader_task.add_done_callback(self._close_waiter.set_result)
        self._encoding = encoding

        self._closing = False
        self._closed = False

    def __repr__(self):
        return '<SSDBConnection [host:{}-port:{}]>'.format(self._address[0], self._address[1])

    @asyncio.coroutine
    def _read_data(self):
        # 在一个套接字生存期中，无限循环，直到断开连接，接收到EOF字符
        # self._reader.at_eof()在调用feed_eof()并且buffer为空的时候为True
        while not self._reader.at_eof():
            try:
                # 调用一个协程读取数据，每次只有全部读取完毕后才会返回数据
                data = yield from self._reader.read(MAX_CHUNK_SIZE)
            except asyncio.CancelledError:
                # 协程被取消，说明连接断开
                break
            except Exception as e:
                logger.error('Exception on data read %r', e, exc_info=True)
                break
            if data == b'' and self._reader.at_eof():
                # 如果读取数据为空，并且reader处于关闭状态，则说明服务器断开连接
                logger.debug('Connection has been closed by server')
            # 在这里解析器工作，解析数据
            self._parser.feed(data)
            # 获取数据,填充期物
            while 1:
                try:
                    obj = self._parser.gets()
                except ProtocolError as e:
                    self._do_close(e)
                    return
                else:
                    if obj is False:
                        break
                    # 这里将获取数据，填充期物（返回值）
                    self._process_data(obj)
        self._closing = True
        self._do_close(None)

    def _process_data(self, obj):
        assert len(self._waiters) > 0, (type(obj), obj)
        waiter, encoding, command = self._waiters.popleft()
        if isinstance(obj, ReplyError):
            obj.command = command
            set_exception(waiter, obj)
        else:
            set_result(waiter, obj)

    def execute(self, command, *args, encoding=_NOTSET):
        '''执行ssdb命令，返回期物等待结果'''
        if self._reader is None or self._reader.at_eof():
            raise ConnectionClosedError("Connection closed or corrupted")
        if command is None:
            raise TypeError("Command must not be None")
        if None in args:
            raise TypeError("args must not contain None")
        # 命令推荐小写
        command = command.lower().strip()

        if encoding is _NOTSET:
            encoding = self._encoding
        future = asyncio.Future(loop=self._loop)
        # 将命令和参数编码成协议要求的格式
        self._writer.write(encode_command(command, *args))
        # 将future进入队列，将来在接收到返回值的时候填充future
        self._waiters.append((future, encoding, command))
        return future

    def auth(self, password):
        future = self.execute('auth', password)
        return wait_ok(future)

    def close(self):
        self._do_close(None)

    def _do_close(self, exc):
        if self._closed:
            return
        self._closing = True
        self._closed = True
        self._writer.transport.close()
        self._reader_task.cancel()
        self._reader_task = None
        self._writer = None
        self._reader = None
        while self._waiters:
            # 将队列中还有的期物弹出并且取消
            waiter, *spam = self._waiters.popleft()
            logger.debug("Cancelling waiter %r", (waiter, spam))
            if exc is None:
                waiter.cancel()
            else:
                waiter.set_exception(exc)

    @asyncio.coroutine
    def wait_closed(self):
        """协程 等待直到连接关闭"""
        yield from asyncio.shield(self._close_waiter, loop=self._loop)

    @property
    def closed(self):
        closed = self._closing or self._closed
        if not closed and self._reader and self._reader.at_eof():
            self._closing = closed = True
            # 立即调用该回调函数
            self._loop.call_soon(self._do_close, None)
        return closed

    @property
    def encoding(self):
        return self._encoding

    @property
    def address(self):
        return self._address
