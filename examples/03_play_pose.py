"""Sotaの頭だけをゆっくり少し動かす。"""

from _common import confirm, parser, robot, run


def main():
    args = parser("Sotaの頭を1秒かけて左右角3度の位置へ動かす").parse_args()
    # HEAD_Yの範囲は-85〜85度。範囲内でも周囲との衝突には注意する。
    pose = {"Msec": 1000, "ServoMap": {"HEAD_Y": 3}}
    confirm()
    print("送信済み。予定時間（ms）:", robot(args).play_pose(pose))


if __name__ == "__main__":
    run(main)
