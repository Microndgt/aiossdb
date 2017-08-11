from .errors import *


def utf8_encode(s):
    """只支持Python3"""
    s = str(s) if isinstance(s, int) else s
    return s.encode('utf8') if isinstance(s, str) else s


def encode_command(command, *args):
    """将命令转换成协议要求的命令格式
    Request := Cmd Blocks*
    Cmd     := Block
    Block  := Size '\n' Data '\n'
    Size   := literal_integer
    Data   := size_bytes_of_data
    比如
        3
        get
        3
        key
    """
    if command == "delete":
        command = "del"

    args = [utf8_encode(command)] + [utf8_encode(i) for i in args]
    buf = utf8_encode('').join(utf8_encode('%d\n%s\n') % (len(i), i) for i in args) + utf8_encode('\n')
    return buf


class SSDBParser:
    def __init__(self, encoding=None):
        # 字节数组
        self.buf = bytearray()
        self.pos = 0
        self._gen = None
        self.encoding = encoding

    def feed(self, data, o=0, l=-1):
        if l == -1:
            l = len(data) - o
        if o < 0 or l < 0:
            raise ValueError("negative input")
        if o + l > len(data):
            raise ValueError("input is larger than buffer size")
        self.buf.extend(data[o:o+l])

    def gets(self):
        """获取解析的数据，或者返回False"""
        return self.parse_one()

    def wait_some(self, size):
        """如果buf长度一直小于所需要的size，则一直迭代False，
        这样就要从套接字来读取数据，直到拿到所有数据"""
        while len(self.buf) < self.pos + size:
            yield False

    def wait_any(self):
        """等待buf进入任意一个字符"""
        yield from self.wait_some(len(self.buf) + 1)

    def read_line(self, size=None):
        if size is not None:
            # size是要读取的数据长度，不会包含\n
            if len(self.buf) < size + 1 + self.pos:
                yield from self.wait_some(size+1)
            offset = self.pos + size
            # 如果请求的该行结束符不是\n的话
            if self.buf[offset:offset+1] != b'\n':
                raise ProtocolError(msg="Expected b'\n'")
        else:
            # 从self.pos开始查找b'\n'的最早出现的位置，如果没有返回-1
            offset = self.buf.find(b'\n', self.pos)
            while offset < 0:
                yield from self.wait_any()
                offset = self.buf.find(b'\n', self.pos)
        val = self.buf[self.pos:offset]
        # 读取一行后重置
        self.pos = 0
        # 删除该行数据
        del self.buf[:offset + 1]
        if self.encoding:
            val = val.decode(self.encoding)
        return val

    def read_int(self):
        """读取协议中定义为数据长度的行"""
        try:
            value = yield from self.read_line()
            return int(value)
        except ValueError:
            raise ProtocolError("Expected int")

    def parse(self):
        size = yield from self.read_int()
        status = yield from self.read_line(size)
        if status != 'ok':
            return ReplyError(status)
        data = []
        try:
            # 可能没有数据，所以在读完状态后的值可能不是int，而是换行符
            # 如果有异常则数据为空
            size = yield from self.read_int()
        except ProtocolError:
            return data
        while True:
            val = yield from self.read_line(size)
            data.append(val)
            try:
                size = yield from self.read_int()
            except ProtocolError:
                break
        return data

    def parse_one(self):
        # 用来驱动生成器获取需要的数据
        # 读取一行，偶数行是数字，奇数行是数据
        if self._gen is None:
            self._gen = self.parse()
        try:
            # 激活协程
            self._gen.send(None)
        except StopIteration as e:
            self._gen = None
            return e.value
        except Exception:
            self._gen = None
            raise
        else:
            return False
