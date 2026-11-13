"""4バイトbig-endianフレーミングと期限付きTCP通信。"""

import json
import math
import select
import socket
import struct
import time

from .errors import CommunicationError, CommunicationTimeout, ProtocolError

MAX_FRAME_BYTES = 64 * 1024 * 1024


def positive_number(value, name):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} は正の有限数で指定してください。")
    return value


def validate_endpoint(host, port, timeout):
    if not isinstance(host, str) or not host.strip():
        raise ValueError("host に接続先IPアドレスまたはホスト名を指定してください。")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("port は1〜65535の整数で指定してください。")
    positive_number(timeout, "timeout（秒）")


def encode_json(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False).encode("ascii")


def decode_json(data):
    try:
        return json.loads(data.decode("utf-8"), parse_constant=_invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("サーバーのJSON応答を解釈できません。") from exc


def _invalid_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def validate_payload(data):
    if not isinstance(data, bytes):
        raise TypeError("フレーム本文はbytesで指定してください。")
    if not 1 <= len(data) <= MAX_FRAME_BYTES:
        raise ValueError(f"フレーム本文は1〜{MAX_FRAME_BYTES}バイトで指定してください。")


def frame(data):
    validate_payload(data)
    return struct.pack(">I", len(data)) + data


class Connection:
    """ソケットを所有する。1インスタンスを複数スレッドから操作しない。"""

    def __init__(self, host, port, timeout):
        validate_endpoint(host, port, timeout)
        self.timeout = timeout
        self.socket = None
        try:
            self.socket = socket.create_connection((host, port), timeout)
            self.socket.settimeout(timeout)
        except OSError as exc:
            self.close()
            self._raise_io(exc)

    @staticmethod
    def _raise_io(exc):
        if isinstance(exc, TimeoutError):
            raise CommunicationTimeout(
                "通信がタイムアウトしました。接続先とサーバーを確認してください。"
            ) from exc
        raise CommunicationError(f"TCP通信に失敗しました: {exc}") from exc

    def send(self, data):
        packet = frame(data)
        try:
            self.socket.sendall(packet)
        except OSError as exc:
            self._raise_io(exc)

    def _exact(self, count, deadline):
        parts = []
        while count:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CommunicationTimeout("応答フレーム全体の受信がタイムアウトしました。")
            self.socket.settimeout(remaining)
            part = self.socket.recv(count)
            if not part:
                raise CommunicationError("応答の途中でTCP接続が切断されました。")
            parts.append(part)
            count -= len(part)
        return b"".join(parts)

    def receive(self, max_bytes=MAX_FRAME_BYTES):
        deadline = time.monotonic() + self.timeout
        try:
            size = struct.unpack(">I", self._exact(4, deadline))[0]
            if not 1 <= size <= min(max_bytes, MAX_FRAME_BYTES):
                raise ProtocolError(f"不正な応答フレーム長です: {size}")
            return self._exact(size, deadline)
        except OSError as exc:
            self._raise_io(exc)
        finally:
            self.socket.settimeout(self.timeout)

    def readable(self, timeout=0):
        try:
            return bool(select.select([self.socket], [], [], timeout)[0])
        except OSError as exc:
            self._raise_io(exc)

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
