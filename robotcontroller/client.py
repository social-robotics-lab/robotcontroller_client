"""RobotControllerの公開操作API。生成時には接続しない。"""

from .errors import ProtocolError
from .protocol import (
    Connection,
    decode_json,
    encode_json,
    positive_number,
    validate_endpoint,
    validate_payload,
)
from .wav import read_wav

SOTA_RANGES = {
    "BODY_Y": (-61, 61),
    "L_SHOU": (-180, 60),
    "L_ELBO": (-90, 65),
    "R_SHOU": (-60, 180),
    "R_ELBO": (-65, 90),
    "HEAD_Y": (-85, 85),
    "HEAD_P": (-27, 5),
    "HEAD_R": (-30, 30),
}
SOTA_LEDS = {
    "PWR_BTN_R",
    "PWR_BTN_G",
    "PWR_BTN_B",
    "R_EYE_R",
    "R_EYE_G",
    "R_EYE_B",
    "L_EYE_R",
    "L_EYE_G",
    "L_EYE_B",
    "MOUTH",
}


def nonnegative_int(value, name):
    if type(value) is not int or not 0 <= value <= 2147483647:
        raise ValueError(f"{name} は0〜2147483647の整数で指定してください。")


class RobotController:
    def __init__(self, host, port=22222, timeout=10.0, *, model="Sota"):
        validate_endpoint(host, port, timeout)
        if model not in ("Sota", None):
            raise ValueError("model は'Sota'またはNoneを指定してください。")
        self.host, self.port, self.timeout, self.model = host, port, timeout, model

    def _command(self, name, payload=None, *, reply=False):
        if payload is not None:
            validate_payload(payload)  # サイズ不正の場合はコマンド名も送らない
        with Connection(self.host, self.port, self.timeout) as connection:
            connection.send(name.encode("ascii"))
            if payload is not None:
                connection.send(payload)
            if reply:
                return decode_json(connection.receive())

    def _validate_pose(self, pose):
        if not isinstance(pose, dict) or "Msec" not in pose:
            raise ValueError("pose はMsecとServoMapまたはLedMapを持つ辞書にしてください。")
        if set(pose) - {"Msec", "ServoMap", "LedMap"}:
            raise ValueError(
                "pose に未知のキーがあります。Msec/ServoMap/LedMapを確認してください。"
            )
        nonnegative_int(pose["Msec"], "Msec（ミリ秒）")
        if not any(pose.get(key) for key in ("ServoMap", "LedMap")):
            raise ValueError("ServoMapまたはLedMapに少なくとも1つの値が必要です。")
        for key in ("ServoMap", "LedMap"):
            mapping = pose.get(key, {})
            if not isinstance(mapping, dict):
                raise ValueError(f"{key} は辞書で指定してください。")
            for name, value in mapping.items():
                if not isinstance(name, str) or not name or type(value) is not int:
                    raise ValueError(f"{key} の名前は文字列、値は整数で指定してください。")
                if not -32768 <= value <= 32767:
                    raise ValueError(f"{name} の値が整数の許容範囲を超えています。")
                if key == "LedMap" and not 0 <= value <= 255:
                    raise ValueError(f"{name} のLED値は0〜255です。")
                if self.model == "Sota":
                    if key == "ServoMap":
                        if (
                            name not in SOTA_RANGES
                            or not SOTA_RANGES[name][0] <= value <= SOTA_RANGES[name][1]
                        ):
                            raise ValueError(f"Sotaの軸名または角度範囲が不正です: {name}={value}")
                    elif name not in SOTA_LEDS:
                        raise ValueError(f"SotaのLED名が不正です: {name}")

    def read_axes(self):
        """軸名→整数角度（度）の辞書を返す。"""
        axes = self._command("read_axes", reply=True)
        if not isinstance(axes, dict) or any(type(v) is not int for v in axes.values()):
            raise ProtocolError("read_axesの応答は軸名と整数角度のJSONオブジェクトが必要です。")
        return axes

    def play_wav(self, path):
        """従来方式でWAV全体を送る。戻り値は長さのミリ秒で、完了通知ではない。"""
        data, duration = read_wav(path)
        self._command("play_wav", data)
        return duration

    def stop_wav(self):
        self._command("stop_wav")

    def play_pose(self, pose):
        self._validate_pose(pose)
        self._command("play_pose", encode_json(pose))
        return pose["Msec"]

    def stop_pose(self):
        self._command("stop_pose")

    def play_motion(self, motion):
        if not isinstance(motion, (list, tuple)) or not motion:
            raise ValueError("motion は空でない姿勢のリストにしてください。")
        for pose in motion:
            self._validate_pose(pose)
        self._command("play_motion", encode_json(motion))
        return sum(pose["Msec"] for pose in motion)

    def stop_motion(self):
        self._command("stop_motion")

    def play_idle_motion(self, speed=1.0, pause=1000):
        positive_number(speed, "speed")
        if not 1 <= 1000 / speed <= 2147483647:
            raise ValueError("speedから求めた動作時間が1〜2147483647ミリ秒の範囲外です。")
        nonnegative_int(pause, "pause（ミリ秒）")
        self._command("play_idle_motion", encode_json({"Speed": speed, "Pause": pause}))

    def stop_idle_motion(self):
        self._command("stop_idle_motion")

    def reset_pose(self, speed=1.0):
        if self.model != "Sota":
            raise ValueError("reset_poseはSota専用です。他機種はplay_poseで指定してください。")
        positive_number(speed, "speed")
        if not 1 <= 1000 / speed <= 2147483647:
            raise ValueError("reset_poseの動作時間が許容範囲外です。")
        return self.play_pose(
            {
                "Msec": int(1000 / speed),
                "ServoMap": {
                    "HEAD_R": 0,
                    "HEAD_P": -5,
                    "HEAD_Y": 0,
                    "BODY_Y": 0,
                    "L_SHOU": -90,
                    "L_ELBO": 0,
                    "R_SHOU": 90,
                    "R_ELBO": 0,
                },
                "LedMap": {key: 255 for key in SOTA_LEDS if "EYE" in key},
            }
        )

    def audio_stream(self):
        """永続接続を開く。withで使用し、終了時に必ず閉じる。"""
        from .audio_stream import AudioStream

        return AudioStream(self.host, self.port, self.timeout)

    def stream_wav(self, path, *, wait=True):
        """WAVを送信。wait=TrueはENDEDまで待機。FalseはPlaybackを返す。"""
        from .audio_stream import Playback

        if type(wait) is not bool:
            raise ValueError("wait はTrueまたはFalseで指定してください。")
        pcm, _ = read_wav(path, streaming=True)
        playback = Playback(self, pcm)
        if wait:
            try:
                playback.wait()
            except BaseException:
                # Ctrl+Cでも送信スレッドを残さず、中止応答または通信期限まで回収する。
                try:
                    playback.close()
                except Exception:
                    pass  # cleanupの通信失敗より最初の例外を優先する
                raise
        return playback
