"""audio_stream_v1のバリア、PCMペーシング、非同期エラー監視。"""

import threading
import time

from .errors import ProtocolError, ServerError
from .protocol import Connection
from .wav import read_wav

BYTES_PER_SECOND = 48000
MAX_PCM_BYTES = 960


def validate_pcm(pcm):
    if not isinstance(pcm, bytes) or not pcm or len(pcm) % 2:
        raise ValueError("PCMは空でない偶数長のbytes（24kHz/mono/S16_LE）で指定してください。")


class AudioStream:
    """同期型ストリーム。スレッド間共有不可。エラー時は接続を閉じる。"""

    def __init__(self, host, port=22222, timeout=10.0):
        self.state = "CONNECTING"
        self._connection = Connection(host, port, timeout)
        try:
            self._connection.send(b"audio_stream_v1")
            self._expect(1)
            self.state = "IDLE"
        except BaseException:
            self.close()
            raise

    def _require(self, state):
        if self.state != state:
            raise ProtocolError(f"操作できない状態です: {self.state}（必要な状態: {state}）")

    def _response(self):
        body = self._connection.receive(max_bytes=2)
        if len(body) != 2:
            raise ProtocolError("音声応答の本文は2バイトである必要があります。")
        kind, code = body
        if kind == 0x81:
            raise ServerError(code)
        if kind != 0x80 or code not in (1, 2, 3, 4):
            raise ProtocolError(f"未知の音声応答です: {body.hex()}")
        return code

    def _expect(self, expected):
        actual = self._response()
        if actual != expected:
            raise ProtocolError(f"音声状態通知が不正です: expected={expected}, actual={actual}")

    def _check_async(self, timeout=0):
        if self._connection.readable(timeout):
            code = self._response()  # ERRORはここで例外になる
            raise ProtocolError(f"DATA送信中に予期しない状態通知を受信しました: {code}")

    def _barrier(self, record, expected, interim, final):
        try:
            self.state = interim
            self._connection.send(record)
            self._expect(expected)
            self.state = final
        except BaseException:
            self.close()
            raise

    def start(self):
        self._require("IDLE")
        self._barrier(b"\x01", 2, "STARTING", "STREAMING")

    def send_pcm(self, pcm, *, _cancel=None, _clock=None, _sleeper=None):
        """START後のPCMを速度制御して送る。形式メタデータは呼び出し側で保証する。

        戻り値FalseはPlaybackからの中止要求、Trueは全DATA送信済み。
        _clock/_sleeperは実機不要のペーシング検証用。
        """
        self._require("STREAMING")
        validate_pcm(pcm)
        clock = _clock or time.monotonic
        schedule_start = clock()
        try:
            for offset in range(0, len(pcm), MAX_PCM_BYTES):
                if _cancel is not None and _cancel.is_set():
                    return False
                chunk = pcm[offset:offset + MAX_PCM_BYTES]
                schedule_offset = offset / BYTES_PER_SECOND
                target = schedule_start + schedule_offset
                delay = target - clock()
                if delay > 0:
                    if _sleeper is None:
                        self._check_async(delay)  # sleep中もERROR/EOFを即座に検出
                    else:
                        _sleeper(delay)
                now = clock()
                if now - target > len(chunk) / BYTES_PER_SECOND:
                    # Phase G既定値と同じ。長い遅延後の追い付きバーストを避ける。
                    schedule_start = now - schedule_offset
                self._check_async()
                if _cancel is not None and _cancel.is_set():
                    return False
                self._connection.send(b"\x02" + chunk)
                self._check_async()
            return True
        except BaseException:
            self.close()
            raise

    def end(self):
        self._require("STREAMING")
        self._barrier(b"\x03", 3, "ENDING", "IDLE")

    def cancel(self):
        self._require("STREAMING")
        self._barrier(b"\x04", 4, "CANCELLING", "IDLE")

    def stream_wav(self, path):
        """同じ接続で順次再生する。ENDEDまで戻らない。"""
        self._require("IDLE")
        pcm, _ = read_wav(path, streaming=True)
        self.start()
        self.send_pcm(pcm)
        self.end()

    def close(self):
        """ソケット解放。活動中なら完了・中止の応答は未確認。"""
        self._connection.close()
        self.state = "CLOSED"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Playback:
    """stream_wavの結果。wait/cancelはワーカースレッドの例外も呼び出し側へ返す。"""

    def __init__(self, robot, pcm):
        self._cancel = threading.Event()
        self._done = threading.Event()
        self._error = None
        self._result = None
        self._thread = threading.Thread(target=self._run, args=(robot, pcm),
                                        name="robotcontroller-playback", daemon=True)
        self._thread.start()

    def _run(self, robot, pcm):
        try:
            with robot.audio_stream() as stream:
                stream.start()
                complete = stream.send_pcm(pcm, _cancel=self._cancel)
                if not complete or self._cancel.is_set():
                    stream.cancel()
                    self._result = "CANCELLED"
                else:
                    stream.end()
                    self._result = "ENDED"
        except BaseException as exc:
            self._error = exc
        finally:
            self._done.set()

    @property
    def done(self):
        return self._done.is_set()

    @property
    def result(self):
        """未完了はNone、成功はENDED、中止完了はCANCELLED。失敗時は例外。"""
        if not self.done:
            return None
        if self._error is not None:
            raise self._error
        return self._result

    def wait(self):
        """サーバーのENDED/CANCELLEDまたは通信エラーまで待つ。"""
        self._thread.join()
        return self.result

    def cancel(self):
        """中止を要求し、ワーカーがCANCELLEDを確認するまで待つ。

        END送信後の要求は正常終了待ちとなる。戻り値を確認すること。
        """
        self._cancel.set()
        return self.wait()

    def close(self):
        return self.cancel()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
