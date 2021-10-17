import json
import jtalk
import random
import serverio as io
from pydub import AudioSegment
from typing import List

HOME_ALL_SERVO_MAP = dict(HEAD_R=0, HEAD_P=-5, HEAD_Y=0, BODY_Y=0, L_SHOU=-90, L_ELBO=0, R_SHOU=90, R_ELBO=0)
HOME_ARM_SERVO_MAP = dict(L_SHOU=-90, L_ELBO=0, R_SHOU=90, R_ELBO=0)
HOME_LED_MAP = dict(L_EYE_R=255, L_EYE_G=255, L_EYE_B=255, R_EYE_R=255, R_EYE_G=255, R_EYE_B=255)
SPEECH_SERVO_MAPS = [
            dict(R_SHOU=59, R_ELBO=23, L_ELBO=-21, L_SHOU=-63),
            dict(R_SHOU=32, R_ELBO=84, L_ELBO=-80, L_SHOU=-16),
            dict(R_SHOU=15, R_ELBO=84, L_ELBO=-76, L_SHOU=-40),
            dict(R_SHOU=57, R_ELBO=20, L_ELBO=-80, L_SHOU=-46),
            dict(R_SHOU=29, R_ELBO=92, L_ELBO=-36, L_SHOU=-74),
            dict(R_SHOU=75, R_ELBO=30, L_ELBO=-31, L_SHOU=-79)
]


def say_text(ip:str, port:int, text:str, speed=1.0, emotion='normal') -> int:
    output_file = '{}.wav'.format(text[:10])
    jtalk.make_wav(text, speed, emotion, output_file, output_dir='wav')
    with open('wav/' + output_file, 'rb') as f:
        data = f.read()
        io.send(ip, port, 'play_wav', data)
    sound = AudioSegment.from_file('wav/' + output_file, 'wav')
    return int(sound.duration_seconds * 1000)

def play_wav(ip:str, port:int, wav_file:str) -> int:
    with open(wav_file, 'rb') as f:
        data = f.read()
        io.send(ip, port, 'play_wav', data)
    sound = AudioSegment.from_file(wav_file, 'wav')
    return int(sound.duration_seconds * 1000)

def stop_wav(ip:str, port:int):
    io.send(ip, port, 'stop_wav')

def play_pose(ip:str, port:int, pose:dict) -> int:
    data = json.dumps(pose).encode('utf-8')
    io.send(ip, port, 'play_pose', data)
    return pose['Msec']

def reset_pose(ip:str, port:int, speed=1.0) -> int:
    msec = int(1000 / speed)
    pose = dict(Msec=msec, ServoMap=HOME_ALL_SERVO_MAP, LedMap=HOME_LED_MAP)
    data = json.dumps(pose).encode('utf-8')
    io.send(ip, port, 'play_pose', data)
    return msec

def stop_pose(ip:str, port:int):
    io.send(ip, port, 'stop_pose')

def read_axes(ip:str, port:int) -> dict:
    data = io.recv(ip, port, 'read_axes')
    axes = json.loads(data)
    return axes

def play_motion(ip:str, port:int, motion:List[dict]) -> int:
    data = json.dumps(motion).encode('utf-8')
    io.send(ip, port, 'play_motion', data)
    return sum(p['Msec'] for p in motion)

def stop_motion(ip:str, port:int):
    io.send(ip, port, 'stop_motion')

def play_idle_motion(ip:str, port:int, speed=1.0, pause=1000):
    data = json.dumps(dict(Speed=speed, Pause=pause)).encode('utf-8')
    io.send(ip, port, 'play_idle_motion', data)
    
def stop_idle_motion(ip:str, port:int):
    io.send(ip, port, 'stop_idle_motion')

def make_speech_motion(duration:int, speed=1.0):
    """
    posedefに定義されているSPEECH_MAPSからランダムに一つ選択し、poseを作る。
    speedはポーズの早さ。msec = 1000/speed
    speedが1.0なら1000msecで動作する。
    """
    def __choose(prev, maps):
        while True:
            map = random.choice(maps)
            if map != prev:
                return map

    msec = int(1000 / speed)
    size = int(duration / msec)
    motion = []
    prev = {}
    for i in range(size):
        map = __choose(prev, SPEECH_SERVO_MAPS)
        motion.append(dict(Msec=msec, ServoMap=map))
        prev = map

    motion.append(dict(Msec=1000, ServoMap=HOME_ARM_SERVO_MAP))
    return motion


