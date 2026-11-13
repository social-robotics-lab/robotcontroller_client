"""新型方式: ENDEDを確認するまで待つ。"""

from _common import SAMPLE_WAV, confirm, parser, robot, run, wav_path


def main():
    command = parser("24kHz/16bit/mono PCM WAVをストリーミング再生する")
    command.add_argument(
        "wav",
        nargs="?",
        type=wav_path,
        default=SAMPLE_WAV,
        help="24kHz・16bit・モノラルWAV（省略時は同梱assets/sample.wav）",
    )
    args = command.parse_args()
    confirm()
    playback = robot(args).stream_wav(args.wav, wait=True)
    print("サーバーの完了通知:", playback.result)


if __name__ == "__main__":
    run(main)
