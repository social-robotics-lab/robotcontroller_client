"""外部素材を使わず、440Hz・0.25秒の小音量テスト音を生成する。再生・通信はしない。"""

import math
import struct
import wave
from pathlib import Path


def generate(path):
    rate = 24000
    frames = 6000
    samples = bytearray()
    for index in range(frames):
        # 最大振幅はフルスケールの約6%。両端10msをフェードしクリックを抑える。
        envelope = min(1.0, index / 240, (frames - 1 - index) / 240)
        value = round(2000 * envelope * math.sin(2 * math.pi * 440 * index / rate))
        samples.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        output.writeframes(samples)


if __name__ == "__main__":
    generate(Path(__file__).with_name("sample.wav"))
