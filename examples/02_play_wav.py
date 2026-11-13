"""従来方式: ファイル全体の送信後に戻る。"""

from _common import SAMPLE_WAV, confirm, parser, robot, run, wav_path


def main():
    command = parser("従来方式でWAVを再生する（完了通知なし）")
    command.add_argument(
        "wav",
        nargs="?",
        type=wav_path,
        default=SAMPLE_WAV,
        help="PCM WAVファイル（省略時は同梱assets/sample.wav）",
    )
    args = command.parse_args()
    confirm()
    duration = robot(args).play_wav(args.wav)
    print(f"送信済み。ファイル長: {duration} ms。再生完了は未確認です。")


if __name__ == "__main__":
    run(main)
