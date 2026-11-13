"""最初に試す読み取り専用サンプル。"""
from _common import parser, robot, run


def main():
    args = parser("現在の関節角度を読み取る（サーボは動かさない）").parse_args()
    print("現在の角度（度）:", robot(args).read_axes())


if __name__ == "__main__":
    run(main)
