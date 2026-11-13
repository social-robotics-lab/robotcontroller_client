"""READMEのWAV実行例をループバックだけで実行し、形式とパスを確認する。"""

import re
import runpy
import shlex
import sys
import wave
from pathlib import Path

import pytest
from conftest import receive, respond

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "assets" / "sample.wav"


def test_generated_asset_format_and_reproduction(tmp_path):
    assert SAMPLE.is_file()
    with wave.open(str(SAMPLE), "rb") as source:
        assert (
            source.getframerate(),
            source.getsampwidth(),
            source.getnchannels(),
            source.getcomptype(),
            source.getnframes(),
        ) == (24000, 2, 1, "NONE", 6000)
    generate = runpy.run_path(str(ROOT / "assets" / "generate_sample.py"))["generate"]
    regenerated = tmp_path / "sample.wav"
    generate(regenerated)
    assert SAMPLE.read_bytes() == regenerated.read_bytes()


@pytest.mark.parametrize("filename", ["02_play_wav.py", "05_audio_stream.py"])
@pytest.mark.parametrize("other_cwd", [False, True])
@pytest.mark.parametrize("use_default", [False, True])
def test_readme_audio_commands(server, monkeypatch, tmp_path, filename, other_cwd, use_default):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    command = re.search(rf"^python examples/{filename} .+$", readme, flags=re.MULTILINE)
    assert command, "READMEに実行例が必要"
    argv = shlex.split(command.group(0))[1:]
    assert argv[-1] == "assets/sample.wav"
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    script = runpy.run_path(str(ROOT / "examples" / filename))
    monkeypatch.setitem(script["main"].__globals__, "confirm", lambda: None)
    monkeypatch.chdir(tmp_path if other_cwd else ROOT)

    def handler(sock):
        if filename.startswith("02"):
            assert receive(sock) == b"play_wav"
            assert receive(sock) == SAMPLE.read_bytes()
        else:
            assert receive(sock) == b"audio_stream_v1"
            respond(sock, 1)
            assert receive(sock) == b"\x01"
            respond(sock, 2)
            pcm = bytearray()
            while True:
                record = receive(sock)
                if record == b"\x03":
                    break
                assert record[0] == 2 and 3 <= len(record) <= 961
                pcm.extend(record[1:])
            with wave.open(str(SAMPLE), "rb") as source:
                assert pcm == source.readframes(source.getnframes())
            respond(sock, 3)
        assert sock.recv(1) == b""

    with server(handler) as port:
        argv[argv.index("--host") + 1] = "127.0.0.1"
        if use_default:
            argv.pop()
        argv.extend(["--port", str(port)])
        monkeypatch.setattr(sys, "argv", argv)
        script["main"]()
