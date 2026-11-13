import threading
from unittest.mock import Mock

import pytest
from conftest import no_frame, receive, respond

from robotcontroller import (
    CommunicationError,
    CommunicationTimeout,
    ProtocolError,
    RobotController,
    ServerError,
)
from robotcontroller.audio_stream import AudioStream


def handshake(sock):
    assert receive(sock) == b"audio_stream_v1"
    respond(sock, 1)


def start(sock):
    assert receive(sock) == b"\x01"
    respond(sock, 2)


def test_gated_barriers_and_consecutive_audio(server, wav_file):
    def handler(sock):
        assert receive(sock) == b"audio_stream_v1"
        no_frame(sock)  # CONNECTION_READYが届くまでSTART禁止
        respond(sock, 1)
        for _ in range(2):
            assert receive(sock) == b"\x01"
            no_frame(sock)  # STARTEDが届くまでDATA禁止
            respond(sock, 2)
            for _ in range(2):
                assert receive(sock) == b"\x02" + b"\x00" * 960
            assert receive(sock) == b"\x03"
            no_frame(sock)  # ENDEDが届くまで次のSTART禁止
            respond(sock, 3)
        assert sock.recv(1) == b""

    path = wav_file()
    with server(handler) as port, AudioStream("127.0.0.1", port) as stream:
        stream.stream_wav(path)
        assert stream.state == "IDLE"
        stream.stream_wav(path)
    assert stream.state == "CLOSED"


def test_wait_false_waits_for_ended(server, wav_file):
    at_end = threading.Event()
    release = threading.Event()

    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock)[0] == 2
        assert receive(sock) == b"\x03"
        at_end.set()
        assert release.wait(2)
        respond(sock, 3)

    with server(handler) as port:
        playback = RobotController("127.0.0.1", port).stream_wav(wav_file(frames=480), wait=False)
        try:
            assert at_end.wait(2)
            assert not playback.done
            assert playback.result is None
        finally:
            release.set()
        assert playback.wait() == "ENDED"
        assert playback.done
        assert playback.close() == "ENDED"


def test_wait_true_uses_ended(server, wav_file):
    at_end = threading.Event()
    finished = threading.Event()
    release = threading.Event()
    errors = []

    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock)[0] == 2
        assert receive(sock) == b"\x03"
        at_end.set()
        assert release.wait(2)
        respond(sock, 3)

    with server(handler) as port:
        path = wav_file(frames=10)

        def play():
            try:
                result = RobotController("127.0.0.1", port).stream_wav(path)
                assert result.result == "ENDED"
            except BaseException as exc:
                errors.append(exc)
            finally:
                finished.set()

        thread = threading.Thread(target=play)
        thread.start()
        try:
            assert at_end.wait(2)
            assert not finished.wait(0.05)  # nominal duration < 1msでも完了しない
        finally:
            release.set()
            thread.join(2)
        assert finished.is_set()
        assert not errors


def test_cancel_then_restart(server):
    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock) == b"\x02\x00\x00"
        assert receive(sock) == b"\x04"
        no_frame(sock)
        respond(sock, 4)
        start(sock)
        assert receive(sock) == b"\x02\x01\x00"
        assert receive(sock) == b"\x03"
        respond(sock, 3)

    with server(handler) as port, AudioStream("127.0.0.1", port) as stream:
        stream.start()
        stream.send_pcm(b"\x00\x00")
        stream.cancel()
        assert stream.state == "IDLE"
        stream.start()
        stream.send_pcm(b"\x01\x00")
        stream.end()


def test_background_cancel_waits_for_cancelled(server, wav_file):
    data_received = threading.Event()
    cancelled = threading.Event()
    release = threading.Event()

    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock)[0] == 2
        data_received.set()
        while True:
            record = receive(sock)
            if record == b"\x04":
                break
            assert record[0] == 2
        cancelled.set()
        assert release.wait(2)
        respond(sock, 4)

    with server(handler) as port:
        playback = RobotController("127.0.0.1", port).stream_wav(wav_file(frames=48000), wait=False)
        assert data_received.wait(2)
        thread = threading.Thread(target=playback.cancel)
        thread.start()
        try:
            assert cancelled.wait(2)
            assert not playback.done
        finally:
            release.set()
            thread.join(2)
        assert playback.wait() == "CANCELLED"


@pytest.mark.parametrize("code", [1, 2, 3, 4, 255])
def test_server_errors_at_handshake(server, code):
    def handler(sock):
        assert receive(sock) == b"audio_stream_v1"
        respond(sock, code, kind=0x81)
        assert sock.recv(1) == b""

    with server(handler) as port, pytest.raises(ServerError) as caught:
        AudioStream("127.0.0.1", port)
    assert caught.value.code == code


@pytest.mark.parametrize("code", [2, 3, 4])
def test_async_errors_stop_data(server, code):
    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock)[0] == 2
        respond(sock, code, kind=0x81)
        # ネットワーク内に既に出たDATAは許すが、ENDは送ってはいけない。
        while True:
            header = sock.recv(4)
            if not header:
                break
            from conftest import exact

            header += exact(sock, 4 - len(header))
            assert exact(sock, int.from_bytes(header, "big"))[0] == 2

    with server(handler) as port:
        with AudioStream("127.0.0.1", port) as stream:
            stream.start()
            with pytest.raises(ServerError) as caught:
                stream.send_pcm(b"\x00" * 96000)
            assert caught.value.code == code
            assert stream.state == "CLOSED"


@pytest.mark.parametrize("body", [b"\x80\x03", b"\x80\xff", b"\x82\x01", b"\x80", b"\x80\x01\x00"])
def test_bad_response(server, body):
    def handler(sock):
        assert receive(sock) == b"audio_stream_v1"
        sock.sendall(len(body).to_bytes(4, "big") + body)

    with server(handler) as port, pytest.raises(ProtocolError):
        AudioStream("127.0.0.1", port)


@pytest.mark.parametrize("terminal", ["end", "cancel"])
def test_terminal_timeout_not_success(server, terminal):
    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock) == (b"\x03" if terminal == "end" else b"\x04")
        assert sock.recv(1) == b""  # 応答せず、クライアントのタイムアウトを待つ

    with server(handler) as port, AudioStream("127.0.0.1", port, 0.1) as stream:
        stream.start()
        with pytest.raises(CommunicationTimeout):
            getattr(stream, terminal)()
        assert stream.state == "CLOSED"


def test_end_disconnect_propagates_to_playback(server, wav_file):
    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock)[0] == 2
        assert receive(sock) == b"\x03"

    with server(handler) as port, pytest.raises(CommunicationError):
        RobotController("127.0.0.1", port).stream_wav(wav_file(frames=1))


def test_wrong_terminal_status(server):
    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock) == b"\x03"
        respond(sock, 4)

    with server(handler) as port, AudioStream("127.0.0.1", port) as stream:
        stream.start()
        with pytest.raises(ProtocolError):
            stream.end()
        assert stream.state == "CLOSED"


@pytest.mark.parametrize("phase", ["start", "end", "cancel"])
@pytest.mark.parametrize("code", [2, 3, 4])
def test_barrier_server_error_closes(server, phase, code):
    def handler(sock):
        handshake(sock)
        if phase == "start":
            assert receive(sock) == b"\x01"
        else:
            start(sock)
            assert receive(sock) == (b"\x03" if phase == "end" else b"\x04")
        respond(sock, code, kind=0x81)
        assert sock.recv(1) == b""

    with server(handler) as port, AudioStream("127.0.0.1", port) as stream:
        if phase != "start":
            stream.start()
        with pytest.raises(ServerError) as caught:
            getattr(stream, phase)()
        assert caught.value.code == code
        assert stream.state == "CLOSED"


def test_invalid_local_transitions(server):
    def handler(sock):
        handshake(sock)
        start(sock)
        assert receive(sock) == b"\x04"
        respond(sock, 4)

    with server(handler) as port, AudioStream("127.0.0.1", port) as stream:
        for action in (stream.end, stream.cancel, lambda: stream.send_pcm(b"\0\0")):
            with pytest.raises(ProtocolError):
                action()
        stream.start()
        with pytest.raises(ProtocolError):
            stream.start()
        stream.cancel()


@pytest.mark.parametrize("pcm", [b"", b"x", "xx", bytearray(b"xx")])
def test_invalid_pcm(pcm):
    stream = AudioStream.__new__(AudioStream)
    stream.state = "STREAMING"
    with pytest.raises(ValueError):
        stream.send_pcm(pcm)


class Clock:
    now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, delay):
        self.now += delay


@pytest.mark.parametrize("stall", [False, True])
def test_pacing_absolute_schedule_and_rebase(stall):
    clock = Clock()
    sent = []

    def send(record):
        sent.append((clock.now, record))
        clock.now += 0.05 if stall and len(sent) == 2 else 0.003

    stream = AudioStream.__new__(AudioStream)
    stream.state = "STREAMING"
    stream._connection = Mock()
    stream._connection.readable.return_value = False
    stream._connection.send.side_effect = send
    stream.send_pcm(b"\0" * (960 * 4 + 2), _clock=clock.monotonic, _sleeper=clock.sleep)
    assert [len(record) for _, record in sent] == [961, 961, 961, 961, 3]
    expected = [0, 0.02, 0.07, 0.09, 0.11] if stall else [0, 0.02, 0.04, 0.06, 0.08]
    assert [stamp for stamp, _ in sent] == pytest.approx(expected)
