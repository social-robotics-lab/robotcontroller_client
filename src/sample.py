import argparse
import client as cl
import time

# MOTION
# motionとは、poseの系列。poseは、各関節の角度指令値(map)と到達時間(msec)の辞書
NOD_MOTION = [
    {"Msec": 250, "ServoMap":{"R_SHOU":105,"HEAD_P":-15,"R_ELBO":0,"L_ELBO":-3,"L_SHOU":-102}},
    {"Msec": 250, "ServoMap":{"R_SHOU":77,"HEAD_P":20,"R_ELBO":17,"L_ELBO":-17,"L_SHOU":-79}},
    {"Msec": 250, "ServoMap":{"R_SHOU":92,"HEAD_P":-5,"R_ELBO":5,"L_ELBO":-7,"L_SHOU":-88}},
]

if __name__ == '__main__':
    # Commadline option
    parse = argparse.ArgumentParser()
    parse.add_argument('--host', required=True)
    parse.add_argument('--port', default=22222, type=int)
    args = parse.parse_args()

    # Global variables
    HOST = args.host
    PORT = args.port

    # Say command
    text = 'おはようございます。ぼくはソータです。どうぞよろしくお願いします。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    time.sleep(t / 1000 + 3)

    # Play wav command
    text = 'サンプルのWavファイルを再生します。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    time.sleep(t / 1000 + 1)
    t = cl.play_wav(HOST, PORT, 'sample.wav')
    print('Sample.wav', 'time:', t)
    time.sleep(t / 1000 + 3)

    # Pose command (Servo)
    text = '2秒間で、45度回転し、左手を90度あげます。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    pose = {'Msec': 2000, 'ServoMap': {'BODY_Y': -45, 'L_SHOU': 0}}
    cl.play_pose(HOST, PORT, pose)
    time.sleep(t / 1000 + 3)

    # Pose command (LED)
    text = '目の色も変えられます。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    pose = {'Msec': 500, 'LedMap': {'L_EYE_R': 0, 'L_EYE_G': 0, 'L_EYE_B': 255, 'R_EYE_R': 0, 'R_EYE_G': 0, 'R_EYE_B': 255}}
    cl.play_pose(HOST, PORT, pose)
    time.sleep(t / 1000 + 3)

    # Read command
    text = '今の関節角度をコンソールに表示しています。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    axes = cl.read_axes(HOST, PORT)
    print('Robot Axes:', axes)
    time.sleep(t / 1000 + 3)

    # Pose command
    text = '関節角度をリセットして、目の色も戻します。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    cl.reset_pose(HOST, PORT)
    time.sleep(t / 1000 + 3)

    # Motion command
    text = 'うなずきモーションを実行します。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    time.sleep(t / 1000 + 1)
    t = cl.play_motion(HOST, PORT, NOD_MOTION)
    print('Nod motion', 'time:', t)
    time.sleep(t / 1000 + 3)

    # Idle motion
    text = 'アイドルモーションを実行します。10秒間様子を見てください。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    cl.play_idle_motion(HOST, PORT, speed=1.0, pause=2000)
    time.sleep(t / 1000 + 10)

    # Stop Idle motion
    text = 'アイドルモーションを停止します。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    cl.stop_idle_motion(HOST, PORT)
    time.sleep(t / 1000 + 3)

    # Say with motion
    text = '''\
    発話しながら、適当なモーションを自動でつけることもできます。\
    ちなみに、アイドルモーションを実行していると、\
    途中でアイドルモーションに割り込まれてしまうので、\
    アイドルモーションは停止してから実行しましょう。\
    '''
    text = text.replace(' ', '')
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    cl.play_motion(HOST, PORT, cl.make_speech_motion(t))
    time.sleep(t / 1000 + 3)

    # Finish
    text = 'これで、機能の説明は終了です。ありがとうございました。'
    t = cl.say_text(HOST, PORT, text)
    print(text, 'time:', t)
    time.sleep(t / 1000)