import json
import jtalk
import posedef
import random
import socket
import threading
from pydub import AudioSegment


class RCClinet(object):
    """
    RobotControllerを操作するためのクラス
    """
    def __init__(self, ip, speech_port=22222, pose_port=22223, read_port=22224):
        self.ip = ip
        self.speech_port = speech_port
        self.pose_port   = pose_port
        self.read_port   = read_port
        self.stop_motion_events = []


    def say(self, text, speed=1.0, emotion='normal'):
        """
        発話させる。
        """
        output_file = '{}_say.wav'.format(self.ip)
        jtalk.make_wav(text, speed, emotion, output_file)
        with open(output_file, 'rb') as f:
            data = f.read()
            send(self.ip, self.speech_port, data)
        sound = AudioSegment.from_file(output_file, 'wav')
        return sound.duration_seconds


    def play_wav(self, wav_file):
        """
        音声ファイルを再生する。
        """
        with open(wav_file, 'rb') as f:
            data = f.read()
            send(self.ip, self.speech_port, data)
        sound = AudioSegment.from_file(wav_file, 'wav')
        return sound.duration_seconds


    def read_axes(self):
        """
        現在の全関節の角度値を読む。
        """
        data = recv(self.ip, self.read_port)
        axes = json.loads(data)
        return axes


    def play_pose(self, pose):
        data = json.dumps(pose).encode('utf-8')
        send(self.ip, self.pose_port, data)
        return pose['Msec']


    def play_motion(self, motion):
        """
        モーションを実行する。
        """
        def play(stop_motion_event):
            for pose in motion:
                data = json.dumps(pose).encode('utf-8')
                send(self.ip, self.pose_port, data)
                sec = pose['Msec'] / 1000.0
                stop_motion_event.wait(sec)
                if stop_motion_event.is_set():
                    break

        self.stop_all_motions()
        stop_motion_event = threading.Event()
        self.stop_motion_events.append(stop_motion_event)
        thread = threading.Thread(target=play, args=(stop_motion_event,))
        thread.start()
        return sum(pose['Msec'] for pose in motion) / 1000
        

    def play_idle_motion(self, speed=0.5, pause=0.5):
        """
        アイドルモーションを実行する関数。
        stop_motionを実行するまでアイドルモーションを続ける。
        """
        def make_pose():
            """
            posedefに定義されているIDLE_MAPSから適切なものを一つ選択し、poseを作る。
            適切なものとは、現在の頭の傾きとは逆方向の頭の傾きのもの、とする。
            （頭がゆらゆら揺れるように見せたいため）
            """
            axes = self.read_axes()
            msec = int(1000 / speed)
            maps = [m for m in posedef.IDLE_MAPS if (m['HEAD_R'] >= 0 if axes['HEAD_R'] < 0 else m['HEAD_R'] < 0)]
            idle_map = random.choice(maps) if maps else posedef.HOME_SERVO_MAP
            pose = dict(Msec=msec, ServoMap=idle_map)
            return pose

        def play(stop_motion_event):
            while not stop_motion_event.is_set():
                pose = make_pose()
                data = json.dumps(pose).encode('utf-8')
                send(self.ip, self.pose_port, data)
                stop_motion_event.wait(1.0 / speed)
                if pause > 0:
                    stop_motion_event.wait(pause)

        self.stop_all_motions()
        stop_motion_event = threading.Event()
        self.stop_motion_events.append(stop_motion_event)
        thread = threading.Thread(target=play, args=(stop_motion_event,))
        thread.start()
        return stop_motion_event


    def play_speech_motion(self, duration, speed=1.0):
        """
        発話中のモーションを実行する関数。
        durationで指定した時間だけモーションを続ける。
        """
        def make_pose():
            """
            posedefに定義されているSPEECH_MAPSからランダムに一つ選択し、poseを作る。
            speedはポーズの早さ。msec = 1000/speed
            speedが1.0なら1000msecで動作する。
            """
            speech_map = random.choice(posedef.SPEECH_MAPS)
            msec = int(1000 / speed)
            pose = dict(Msec=msec, ServoMap=speech_map)
            return pose

        def play(stop_motion_event):
            sec = 1.0 / speed
            remaining_time = duration
            while remaining_time > sec:
                pose = make_pose()
                data = json.dumps(pose).encode('utf-8')
                send(self.ip, self.pose_port, data)
                stop_motion_event.wait(sec)
                if stop_motion_event.is_set():
                    break
                remaining_time -= sec

        self.stop_all_motions()
        stop_motion_event = threading.Event()
        self.stop_motion_events.append(stop_motion_event)
        thread = threading.Thread(target=play, args=(stop_motion_event,))
        thread.start()
        return stop_motion_event


    def stop_all_motions(self):
        for e in self.stop_motion_events:
            e.set()
        self.stop_motion_events.clear()


    def reset_pose(self, speed=1.0):
        """
        ポーズをホームポジションに戻す関数。
        """
        msec = int(1000 / speed)
        pose = dict(Msec=msec, ServoMap=posedef.HOME_SERVO_MAP, LedMap=posedef.HOME_LED_MAP)
        data = json.dumps(pose).encode('utf-8')
        send(self.ip, self.pose_port, data)



#---------------------
# Low level functions
#---------------------

def recv(ip, port):
    conn = connect(ip, port)
    size = read_size(conn)
    data = read_data(conn, size)
    close(conn)
    return data.decode('utf-8')

def send(ip, port, data):
    conn = connect(ip, port)
    size = len(data)
    conn.send(size.to_bytes(4, byteorder='big'))
    conn.send(data)
    close(conn)

def connect(ip, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((ip, port))
    return conn

def close(conn):
    conn.shutdown(1)
    conn.close()

def read_size(conn):
    b_size = conn.recv(4)
    return int.from_bytes(b_size, byteorder='big')

def read_data(conn, size):
    chunks = []
    bytes_recved = 0
    while bytes_recved < size:
        chunk = conn.recv(size - bytes_recved)
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recved += len(chunk)
    return b''.join(chunks)