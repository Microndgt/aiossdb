class SSDBError(Exception):
    """aiossdb异常基类"""


class ConnectionClosedError(SSDBError):
    """如果到服务器的连接被关闭引发该异常"""


class ReplyError(SSDBError):
    """ssdb服务器返回的错误类型，可能有:
       not_found, error, fail, client_error
    """
    def __int__(self, etype, command=None):
        self.etype = etype
        self.command = command


class ProtocolError(SSDBError):
    """当解析协议出现问题时候引发该异常"""
    def __init__(self, msg):
        self.msg = msg


class PoolClosedError(SSDBError):
    """如果连接池已经关闭，引发该异常"""
