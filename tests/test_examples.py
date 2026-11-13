"""サンプルのimportとTTS連携を、通信・外部実行なしで検証。"""

import io
import runpy
import sys
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as target:
        target.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        target.writeframes(b"\0\0" * 100)
    return buffer.getvalue()


def load(monkeypatch, filename):
    monkeypatch.syspath_prepend(str(EXAMPLES))
    return runpy.run_path(str(EXAMPLES / filename))


@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("[0-9]*.py")))
def test_examples_import_and_help_only(monkeypatch, path):
    script = load(monkeypatch, path.name)
    monkeypatch.setattr(sys, "argv", [str(path), "--help"])
    with pytest.raises(SystemExit) as caught:
        script["main"]()
    assert caught.value.code == 0


def test_azure_without_credentials_does_not_import_sdk(monkeypatch):
    script = load(monkeypatch, "07_azure_tts.py")
    monkeypatch.setattr(sys, "argv", ["sample", "--host", "127.0.0.1", "こんにちは"])
    monkeypatch.delenv("SPEECH_KEY", raising=False)
    monkeypatch.delenv("SPEECH_REGION", raising=False)
    with pytest.raises(ValueError, match="SPEECH_KEY"):
        script["main"]()


def test_gtts_conversion_and_streaming(monkeypatch):
    script = load(monkeypatch, "06_gtts.py")
    main = script["main"]
    calls = []
    streamed = []

    class Speech:
        def __init__(self, text, lang):
            assert text == "こんにちは" and lang == "ja"

        def save(self, path):
            Path(path).write_bytes(b"fake-mp3")

    def convert(args, **kwargs):
        assert kwargs == {"check": True}
        assert args[args.index("-ar") + 1] == "24000"
        assert args[args.index("-ac") + 1] == "1"
        assert args[args.index("-c:a") + 1] == "pcm_s16le"
        calls.append(args)
        Path(args[-1]).write_bytes(wav_bytes())

    def stream(path):
        streamed.append(Path(path).read_bytes())
        return SimpleNamespace(result="ENDED")

    monkeypatch.setattr(sys, "argv", ["sample", "--host", "127.0.0.1", "こんにちは"])
    monkeypatch.setitem(sys.modules, "gtts", SimpleNamespace(gTTS=Speech))
    monkeypatch.setitem(main.__globals__, "confirm", lambda: None)
    monkeypatch.setitem(main.__globals__, "robot", lambda args: SimpleNamespace(stream_wav=stream))
    monkeypatch.setattr(script["shutil"], "which", lambda value: "fake-ffmpeg")
    monkeypatch.setattr(script["subprocess"], "run", convert)
    main()
    assert len(calls) == 1 and streamed == [wav_bytes()]
    assert not Path(calls[0][-1]).exists()  # 一時ファイル解放


def test_azure_format_and_no_speaker(monkeypatch):
    script = load(monkeypatch, "07_azure_tts.py")
    main = script["main"]
    config = Mock()
    synth = Mock()
    synth.speak_text_async.return_value.get.return_value = SimpleNamespace(
        reason="complete", audio_data=wav_bytes()
    )
    sdk = SimpleNamespace(
        SpeechConfig=Mock(return_value=config),
        SpeechSynthesizer=Mock(return_value=synth),
        SpeechSynthesisOutputFormat=SimpleNamespace(Riff24Khz16BitMonoPcm="riff24"),
        ResultReason=SimpleNamespace(SynthesizingAudioCompleted="complete"),
    )
    azure = SimpleNamespace(cognitiveservices=SimpleNamespace(speech=sdk))
    monkeypatch.setitem(sys.modules, "azure", azure)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices", azure.cognitiveservices)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices.speech", sdk)
    monkeypatch.setenv("SPEECH_KEY", "test-placeholder")
    monkeypatch.setenv("SPEECH_REGION", "test-region")
    monkeypatch.setattr(sys, "argv", ["sample", "--host", "127.0.0.1", "こんにちは"])
    monkeypatch.setitem(main.__globals__, "confirm", lambda: None)
    streamed = []

    def stream(path):
        streamed.append(Path(path).read_bytes())
        return SimpleNamespace(result="ENDED")

    monkeypatch.setitem(main.__globals__, "robot", lambda args: SimpleNamespace(stream_wav=stream))
    main()
    config.set_speech_synthesis_output_format.assert_called_once_with("riff24")
    sdk.SpeechSynthesizer.assert_called_once_with(speech_config=config, audio_config=None)
    assert streamed == [wav_bytes()]
