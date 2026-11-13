import json
from unittest.mock import Mock

import pytest
from conftest import receive

from robotcontroller import ProtocolError, RobotController
from robotcontroller.helpers import make_beat_motion
from robotcontroller.protocol import frame
from robotcontroller.wav import read_wav

POSE = {"Msec": 1000, "ServoMap": {"HEAD_Y": 3}}


@pytest.mark.parametrize(
    "command",
    [
        "play_wav",
        "stop_wav",
        "play_pose",
        "stop_pose",
        "play_motion",
        "stop_motion",
        "play_idle_motion",
        "stop_idle_motion",
        "read_axes",
    ],
)
def test_nine_commands(server, wav_file, command):
    wav = wav_file()
    expected = {
        "play_wav": wav.read_bytes(),
        "play_pose": POSE,
        "play_motion": [POSE],
        "play_idle_motion": {"Speed": 1.0, "Pause": 1000},
    }

    def handler(sock):
        assert receive(sock) == command.encode("ascii")
        if command in expected:
            data = receive(sock)
            assert (data if command == "play_wav" else json.loads(data)) == expected[command]
        if command == "read_axes":
            sock.sendall(frame(b'{"HEAD_Y":3}'))
        assert sock.recv(1) == b""  # 一接続一コマンド、ACKを待たない

    with server(handler) as port:
        robot = RobotController("127.0.0.1", port)
        args = {"play_wav": (wav,), "play_pose": (POSE,), "play_motion": ([POSE],)}
        result = getattr(robot, command)(*args.get(command, ()))
    if command == "play_wav":
        assert result == 40
    elif command in ("play_pose", "play_motion"):
        assert result == 1000
    elif command == "read_axes":
        assert result == {"HEAD_Y": 3}
    else:
        assert result is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"host": ""},
        {"host": "x", "port": 0},
        {"host": "x", "port": True},
        {"host": "x", "timeout": 0},
        {"host": "x", "timeout": float("nan")},
        {"host": "x", "model": "Unknown"},
    ],
)
def test_endpoint_validation(kwargs):
    with pytest.raises(ValueError):
        RobotController(**kwargs)


def test_construct_does_not_connect(monkeypatch):
    connect = Mock(side_effect=AssertionError("must not connect"))
    monkeypatch.setattr("socket.create_connection", connect)
    RobotController("192.0.2.1")
    connect.assert_not_called()


def test_payload_limit_checked_before_connect(monkeypatch):
    connect = Mock(side_effect=AssertionError("must not connect"))
    monkeypatch.setattr("socket.create_connection", connect)
    monkeypatch.setattr("robotcontroller.protocol.MAX_FRAME_BYTES", 4)
    with pytest.raises(ValueError):
        RobotController("127.0.0.1").play_pose(POSE)
    connect.assert_not_called()


@pytest.mark.parametrize(
    "pose",
    [
        {},
        {"Msec": -1, "ServoMap": {"HEAD_Y": 0}},
        {"Msec": True, "ServoMap": {"HEAD_Y": 0}},
        {"Msec": 1},
        {"Msec": 1, "ServoMap": {"HEAD_P": 20}},
        {"Msec": 1, "ServoMap": {"R_ELBO": 92}},
        {"Msec": 1, "ServoMap": {"UNKNOWN": 0}},
        {"Msec": 1, "LedMap": {"MOUTH": 256}},
        {"Msec": 1, "ServoMap": {"HEAD_Y": 1.5}},
        {"Msec": 1, "ServoMap": []},
        {"Msec": 1, "ServoMap": {"HEAD_Y": 0}, "Typo": 1},
    ],
)
def test_invalid_pose_does_not_send(pose, monkeypatch):
    robot = RobotController("127.0.0.1")
    send = Mock()
    monkeypatch.setattr(robot, "_command", send)
    with pytest.raises(ValueError):
        robot.play_pose(pose)
    send.assert_not_called()


@pytest.mark.parametrize("speed", [0, -1, True, float("inf"), float("nan"), 1001, 1e-12])
def test_invalid_speed(speed):
    with pytest.raises(ValueError):
        RobotController("127.0.0.1").play_idle_motion(speed=speed)


@pytest.mark.parametrize("payload", [b"[]", b'{"HEAD_Y":1.5}', b'{"HEAD_Y":true}'])
def test_axes_response_type(server, payload):
    def handler(sock):
        assert receive(sock) == b"read_axes"
        sock.sendall(frame(payload))

    with server(handler) as port, pytest.raises(ProtocolError):
        RobotController("127.0.0.1", port).read_axes()


@pytest.mark.parametrize("options", [{"rate": 48000}, {"channels": 2}, {"width": 1}, {"frames": 0}])
def test_stream_wav_format(wav_file, options):
    with pytest.raises(ValueError):
        read_wav(wav_file(**options), streaming=True)


def test_wav_pcm_extraction(wav_file):
    pcm, duration = read_wav(wav_file(), streaming=True)
    assert pcm == b"\x00" * 1920
    assert duration == 40


def test_truncated_wav(wav_file):
    path = wav_file()
    path.write_bytes(path.read_bytes()[:-2])
    with pytest.raises(ValueError):
        read_wav(path, streaming=True)


def test_bad_wav(tmp_path):
    path = tmp_path / "bad.wav"
    path.write_bytes(b"not a WAV")
    with pytest.raises(ValueError):
        read_wav(path)


def test_reset_and_helper(monkeypatch):
    robot = RobotController("127.0.0.1")
    send = Mock()
    monkeypatch.setattr(robot, "_command", send)
    assert robot.reset_pose() == 1000
    assert json.loads(send.call_args.args[1])["ServoMap"]["HEAD_P"] == -5
    for pose in make_beat_motion(3):
        robot._validate_pose(pose)
    with pytest.raises(ValueError):
        RobotController("127.0.0.1", model=None).reset_pose()


def test_other_model_and_invalid_motion(monkeypatch):
    robot = RobotController("127.0.0.1", model=None)
    monkeypatch.setattr(robot, "_command", Mock())
    robot.play_pose({"Msec": 100, "ServoMap": {"BODY_P": 0}})
    for motion in ([], "bad", [POSE, {}]):
        with pytest.raises(ValueError):
            robot.play_motion(motion)
