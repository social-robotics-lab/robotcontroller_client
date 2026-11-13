"""サンプル共通の引数とエラー表示。import時には操作しない。"""
import argparse
import sys

from robotcontroller import RobotController, RobotControllerError


def parser(description):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--host", required=True, help="ロボットのIPアドレス（省略不可）")
    result.add_argument("--port", type=int, default=22222)
    result.add_argument("--timeout", type=float, default=10.0, help="通信タイムアウト（秒）")
    return result


def robot(args):
    return RobotController(args.host, args.port, args.timeout)


def run(main):
    try:
        main()
    except (RobotControllerError, OSError, ValueError, RuntimeError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(1)


def confirm():
    if input("周囲と停止方法を確認し、実行する場合は yes と入力: ") != "yes":
        raise SystemExit("中止しました。")
