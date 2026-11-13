"""全テストの通信をIPv4ループバックに限定する。"""

import socket
import threading
import wave
from contextlib import contextmanager

import pytest


@pytest.fixture(autouse=True)
def loopback_only(monkeypatch):
    original = socket.socket.connect

    def connect(sock, address):
        if not isinstance(address, tuple) or address[0] != "127.0.0.1":
            raise AssertionError(f"テストで外部への接続は禁止: {address}")
        return original(sock, address)

    monkeypatch.setattr(socket.socket, "connect", connect)


def exact(sock, count):
    data = b""
    while len(data) < count:
        part = sock.recv(count - len(data))
        if not part:
            raise AssertionError("Unexpected EOF")
        data += part
    return data


def receive(sock):
    count = int.from_bytes(exact(sock, 4), "big")
    assert 0 < count <= 64 * 1024 * 1024
    return exact(sock, count)


def respond(sock, code, kind=0x80):
    sock.sendall(b"\x00\x00\x00\x02" + bytes((kind, code)))


def no_frame(sock):
    previous = sock.gettimeout()
    sock.settimeout(0.04)
    try:
        with pytest.raises(socket.timeout):
            sock.recv(1)
    finally:
        sock.settimeout(previous)


@pytest.fixture
def server():
    @contextmanager
    def start(handler, connections=1):
        failures = []
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            listener.settimeout(3)

            def serve():
                try:
                    for _ in range(connections):
                        with listener.accept()[0] as sock:
                            sock.settimeout(3)
                            handler(sock)
                except BaseException as exc:
                    failures.append(exc)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            try:
                yield listener.getsockname()[1]
            finally:
                thread.join(4)
                assert not thread.is_alive(), "mock server did not exit"
                if failures:
                    raise failures[0]

    return start


@pytest.fixture
def wav_file(tmp_path):
    def make(*, rate=24000, channels=1, width=2, frames=960, name="sample.wav"):
        path = tmp_path / name
        with wave.open(str(path), "wb") as target:
            target.setparams((channels, width, rate, 0, "NONE", "not compressed"))
            target.writeframes(b"\x00" * frames * channels * width)
        return path

    return make
