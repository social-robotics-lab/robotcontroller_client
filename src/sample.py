import argparse
import time
from client import RCClient
from posedef import NOD_MOTION

# Commadline option
parse = argparse.ArgumentParser()
parse.add_argument('--host', required=True)
parse.add_argument('--speech_port', default=22222, type=int)
parse.add_argument('--pose_port', default=22223, type=int)
parse.add_argument('--read_port', default=22224, type=int)
args = parse.parse_args()

# Global variables
HOST = args.host
SPEECH_PORT = args.speech_port
POSE_PORT = args.pose_port
READ_PORT = args.read_port

c = RCClient(HOST, SPEECH_PORT, POSE_PORT, READ_PORT)


# Say command
text = 'おはようございます。ぼくはソータです。どうぞよろしくお願いします。'
t = c.say(text)
print(text, 'time:', t)
time.sleep(t + 3)

# Play wav command
text = 'サンプルのWavファイルを再生します。'
t = c.say(text)
print(text, 'time:', t)
time.sleep(t + 1)
t = c.play_wav('sample.wav')
print('Sample.wav', 'time:', t)
time.sleep(t + 3)

# Pose command (Servo)
text = '2秒間で、45度回転し、左手を90度あげます。'
t = c.say(text)
print(text, 'time:', t)
pose = {'Msec': 2000, 'ServoMap': {'BODY_Y': -45, 'L_SHOU': 0}}
c.play_pose(pose)
time.sleep(t + 3)

# Pose command (LED)
text = '目の色も変えられます。'
t = c.say(text)
print(text, 'time:', t)
pose = {'Msec': 500, 'LedMap': {'L_EYE_R': 0, 'L_EYE_G': 0, 'L_EYE_B': 255, 'R_EYE_R': 0, 'R_EYE_G': 0, 'R_EYE_B': 255}}
c.play_pose(pose)
time.sleep(t + 3)

# Read command
text = '今の関節角度をコンソールに表示しています。'
t = c.say(text)
print(text, 'time:', t)

axes = c.read_axes()
print('Robot Axes:', axes)
time.sleep(t + 3)

# Pose command
text = '関節角度をリセットして、目の色も戻します。'
t = c.say(text)
print(text, 'time:', t)
c.reset_pose()
time.sleep(t + 3)

# Motion command
text = 'うなずきモーションを実行します。'
t = c.say(text)
print(text, 'time:', t)
time.sleep(t + 1)
t = c.play_motion(NOD_MOTION)
print('Nod motion', 'time:', t)
time.sleep(t + 3)


# Idle motion
text = 'アイドルモーションを実行します。10秒間様子を見てください。'
t = c.say(text)
print(text, 'time:', t)
c.play_idle_motion()
time.sleep(t + 10)

# Say with motion
text = '''\
発話しながら、適当なモーションを自動でつけることもできます。\
ちなみに、プレイスピーチモーションや、プレイモーションを実行すると、\
アイドルモーションは停止します。\
'''
t = c.say(text)
c.play_speech_motion(t)
print(text, 'time:', t)
time.sleep(t + 3)


text = 'これで、機能の説明は終了です。ありがとうございました。'
t = c.say(text)
c.reset_pose()
print(text, 'time:', t)
time.sleep(t)