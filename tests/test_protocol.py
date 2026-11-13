import json
import socket
import struct
import time
from unittest.mock import Mock

import pytest
from conftest import receive

from robotcontroller import CommunicationError, CommunicationTimeout, ProtocolError
from robotcontroller.protocol import Connection, decode_json, encode_json, frame


def test_frame():
    assert frame(b"abc") == b"\x00\x00\x00\x03abc"


@pytest.mark.parametrize("data", [b"", "text", bytearray(b"x")])
def test_invalid_frame(data):
    with pytest.raises((TypeError, ValueError)):
        frame(data)


def test_sendall_and_large_payload(server):
    data = b"x" * (2 * 1024 * 1024)

    def handler(sock):
        assert receive(sock) == data

    with server(handler) as port, Connection("127.0.0.1", port, 2) as connection:
        connection.send(data)


def test_send_uses_sendall(monkeypatch):
    sock = Mock()
    monkeypatch.setattr(socket, "create_connection", lambda *args: sock)
    with Connection("127.0.0.1", 1234, 1) as connection:
        connection.send(b"test")
    sock.sendall.assert_called_once_with(frame(b"test"))
    sock.send.assert_not_called()
    sock.close.assert_called_once()


def test_partial_header_and_body(server):
    packet = frame(encode_json({"名前": "ソータ"}))

    def handler(sock):
        for value in packet:
            sock.sendall(bytes([value]))

    with server(handler) as port, Connection("127.0.0.1", port, 2) as connection:
        assert decode_json(connection.receive()) == {"名前": "ソータ"}


@pytest.mark.parametrize("size", [0, 0x80000000, 64 * 1024 * 1024 + 1])
def test_invalid_lengths(server, size):
    with server(lambda sock: sock.sendall(struct.pack(">I", size))) as port:
        with Connection("127.0.0.1", port, 1) as connection, pytest.raises(ProtocolError):
            connection.receive()


@pytest.mark.parametrize("packet", [b"", b"\x00\x00", b"\x00\x00\x00\x04ab"])
def test_eof(server, packet):
    with server(lambda sock: sock.sendall(packet)) as port:
        with Connection("127.0.0.1", port, 1) as connection, pytest.raises(CommunicationError):
            connection.receive()


def test_timeout(server):
    def handler(sock):
        time.sleep(0.12)

    with server(handler) as port:
        with Connection("127.0.0.1", port, 0.03) as connection:
            with pytest.raises(CommunicationTimeout):
                connection.receive()


def test_total_frame_deadline(server):
    def handler(sock):
        for part in (b"\x00", b"\x00", b"\x00", b"\x02", b"ab"):
            try:
                sock.sendall(part)
            except OSError:
                break
            time.sleep(0.04)

    with server(handler) as port:
        with Connection("127.0.0.1", port, 0.07) as connection:
            with pytest.raises(CommunicationTimeout):
                connection.receive()


@pytest.mark.parametrize("data", [b"{", b"\xff", b"NaN", b"Infinity"])
def test_invalid_json(data):
    with pytest.raises(ProtocolError):
        decode_json(data)


def test_json_encoding():
    packet = encode_json({"日本語": 1})
    assert packet.isascii()
    assert json.loads(packet) == {"日本語": 1}
    with pytest.raises(ValueError):
        encode_json(float("nan"))


@pytest.mark.parametrize(
    "exc,expected",
    [(TimeoutError(), CommunicationTimeout), (ConnectionRefusedError(), CommunicationError)],
)
def test_connect_failure(monkeypatch, exc, expected):
    monkeypatch.setattr(socket, "create_connection", Mock(side_effect=exc))
    with pytest.raises(expected):
        Connection("127.0.0.1", 1234, 1)


def test_send_timeout_closes_context(monkeypatch):
    sock = Mock()
    sock.sendall.side_effect = TimeoutError()
    monkeypatch.setattr(socket, "create_connection", lambda *args: sock)
    with pytest.raises(CommunicationTimeout):
        with Connection("127.0.0.1", 1234, 1) as connection:
            connection.send(b"x")
    sock.close.assert_called_once()
