"""gTTSのMP3をffmpegで24kHz/mono/S16_LE WAVへ変換する。"""
from pathlib import Path
import shutil
import subprocess
import tempfile

from _common import confirm, parser, robot, run


def main():
    command = parser("gTTSで日本語を合成して再生する（インターネット接続が必要）")
    command.add_argument("text", help="読み上げる日本語。外部サービスへ送信されます")
    args = command.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpegをインストールしてPATHへ追加してください。READMEを参照。")
    try:
        from gtts import gTTS
    except ImportError as exc:
        raise RuntimeError('python -m pip install -e ".[gtts]" を実行してください。') from exc
    confirm()
    with tempfile.TemporaryDirectory() as directory:
        mp3 = Path(directory) / "speech.mp3"
        wav = Path(directory) / "speech.wav"
        gTTS(args.text, lang="ja").save(str(mp3))
        # shellは使用せず、音声形式を明示する。
        try:
            subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-i", str(mp3),
                            "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
                           check=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("ffmpegでの音声変換に失敗しました。") from exc
        print("完了通知:", robot(args).stream_wav(wav).result)


if __name__ == "__main__":
    run(main)
