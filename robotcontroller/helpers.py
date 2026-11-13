"""ネットワーク通信のないSota用モーション生成。"""

from .protocol import positive_number


def make_beat_motion(duration_seconds, speed=1.0):
    """控えめな頭の左右動作を生成。時間は秒、各Msecはミリ秒。

    指定時間を超えない全ステップと、中央に戻す1000msを含む。
    周囲・初期姿勢の安全性は操作者が確認する。
    """
    positive_number(duration_seconds, "duration_seconds")
    positive_number(speed, "speed")
    step = 1000 / speed
    if not 250 <= step <= 2147483647:
        raise ValueError("1ステップが250〜2147483647ミリ秒となるspeedを指定してください。")
    step = int(step)
    count = int(duration_seconds * 1000 / step)
    if count > 10000:
        raise ValueError("生成する姿勢は10000ステップ以下にしてください。")
    return [{"Msec": step, "ServoMap": {"HEAD_Y": 3 if i % 2 == 0 else -3}}
            for i in range(count)] + [{"Msec": 1000, "ServoMap": {"HEAD_Y": 0}}]
