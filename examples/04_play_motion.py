"""腕を動かさない短いSotaモーション。"""
from _common import confirm, parser, robot, run


def main():
    args = parser("Sotaの頭を少し左右に動かし、中央に戻す").parse_args()
    motion = [{"Msec": 1000, "ServoMap": {"HEAD_Y": angle}} for angle in (3, -3, 0)]
    confirm()
    print("送信済み。予定時間（ms）:", robot(args).play_motion(motion))


if __name__ == "__main__":
    run(main)
