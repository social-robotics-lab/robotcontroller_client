"""Azure Speechでストリーム用WAVを合成。PCのスピーカーは使わない。"""

import os
import tempfile
from pathlib import Path

from _common import confirm, parser, robot, run


def main():
    command = parser("Azure Speechで日本語を合成して再生する（課金・認証が必要）")
    command.add_argument("text", help="読み上げる日本語。Azureへ送信されます")
    command.add_argument("--voice", default="ja-JP-NanamiNeural")
    args = command.parse_args()
    key, region = os.environ.get("SPEECH_KEY"), os.environ.get("SPEECH_REGION")
    if not key or not region:
        raise ValueError("環境変数SPEECH_KEYとSPEECH_REGIONを設定してください。")
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError as exc:
        raise RuntimeError('python -m pip install -e ".[azure]" を実行してください。') from exc
    confirm()
    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_synthesis_voice_name = args.voice
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(args.text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"Azure音声合成に失敗しました: {result.reason}")
    with tempfile.TemporaryDirectory() as directory:
        wav = Path(directory) / "speech.wav"
        wav.write_bytes(result.audio_data)
        print("完了通知:", robot(args).stream_wav(wav).result)


if __name__ == "__main__":
    run(main)
