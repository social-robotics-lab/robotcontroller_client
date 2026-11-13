"""サンプル共通の引数とエラー表示。import時には操作しない。"""

import argparse
import sys
from pathlib import Path

from robotcontroller import RobotController, RobotControllerError

SAMPLE_WAV = Path(__file__).resolve().parents[1] / "assets" / "sample.wav"


def wav_path(value):
    """明示パスは通常どおり解決し、同梱assetsパスだけはリポジトリ基準にも対応。"""
    path = Path(value).expanduser()
    if not path.is_absolute() and path.as_posix() == "assets/sample.wav" and not path.is_file():
        return SAMPLE_WAV
    return path


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
        raise SystemExit(1) from None


def confirm():
    if input("周囲と停止方法を確認し、実行する場合は yes と入力: ") != "yes":
        raise SystemExit("中止しました。")
