import argparse
import time
import client
import json

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

# Speech command
with open('sample.wav', 'rb') as f:
    wav_data = f.read()
    client.send(HOST, SPEECH_PORT, wav_data)
time.sleep(3)

# Pose command (Servo)
pose_data = {'Msec': 2000, 'ServoMap': {'BODY_Y': -45, 'L_SHOU': 0}}
client.send(HOST, POSE_PORT, json.dumps(pose_data).encode('utf-8'))
time.sleep(3)

# Pose command (LED)
pose_data = {'Msec': 100, 'LedMap': {'L_EYE_R': 0, 'L_EYE_G': 0, 'L_EYE_B': 255, 'R_EYE_R': 255, 'R_EYE_G': 0, 'R_EYE_B': 0}}
client.send(HOST, POSE_PORT, json.dumps(pose_data).encode('utf-8'))
time.sleep(3)

# Read command
read_data = client.recv(HOST, READ_PORT)
print('Robot Axes:', read_data)
time.sleep(3)

# Pose command
pose_data = {'Msec': 1000, 'ServoMap': {'BODY_Y': 0, 'L_SHOU': -90}, 'LedMap': {'L_EYE_R': 255, 'L_EYE_G': 255, 'L_EYE_B': 255, 'R_EYE_R': 255, 'R_EYE_G': 255, 'R_EYE_B': 255}}
client.send(HOST, POSE_PORT, json.dumps(pose_data).encode('utf-8'))
time.sleep(3)

