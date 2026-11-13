"""新型方式: ENDEDを確認するまで待つ。"""
from _common import confirm, parser, robot, run


def main():
    command = parser("24kHz/16bit/mono PCM WAVをストリーミング再生する")
    command.add_argument("wav", help="24kHz・16bit・モノラルWAV")
    args = command.parse_args()
    confirm()
    playback = robot(args).stream_wav(args.wav, wait=True)
    print("サーバーの完了通知:", playback.result)


if __name__ == "__main__":
    run(main)
