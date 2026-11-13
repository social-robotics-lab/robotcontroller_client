"""WAVコンテナの検証。音声変換は呼び出し側で行う。"""

import io
from pathlib import Path
import wave


def read_wav(path, *, streaming=False):
    data = Path(path).read_bytes()
    try:
        with wave.open(io.BytesIO(data), "rb") as source:
            if streaming and (source.getframerate(), source.getnchannels(),
                              source.getsampwidth(), source.getcomptype()) != (24000, 1, 2, "NONE"):
                raise ValueError("ストリーミングWAVは24kHz・16bit・モノラルの非圧縮PCMが必要です。")
            frames = source.getnframes()
            pcm = source.readframes(frames)
            if frames == 0 or len(pcm) != frames * source.getnchannels() * source.getsampwidth():
                raise ValueError("WAVのPCMが空、または途中で切れています。")
            duration_ms = int(frames * 1000 / source.getframerate())
    except (wave.Error, EOFError) as exc:
        raise ValueError(f"有効なPCM WAVファイルではありません: {path}") from exc
    return (pcm if streaming else data), duration_ms
