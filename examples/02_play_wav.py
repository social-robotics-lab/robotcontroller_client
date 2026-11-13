"""従来方式: ファイル全体の送信後に戻る。"""

from _common import confirm, parser, robot, run


def main():
    command = parser("従来方式でWAVを再生する（完了通知なし）")
    command.add_argument("wav", help="PCM WAVファイル")
    args = command.parse_args()
    confirm()
    duration = robot(args).play_wav(args.wav)
    print(f"送信済み。ファイル長: {duration} ms。再生完了は未確認です。")


if __name__ == "__main__":
    run(main)
