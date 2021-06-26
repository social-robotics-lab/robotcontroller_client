SPEECH_MAPS = [
    {"R_SHOU": 59, "R_ELBO": 23, "L_ELBO": -21, "L_SHOU":-63},
    {"R_SHOU": 32, "R_ELBO": 84, "L_ELBO": -80, "L_SHOU":-16},
    {"R_SHOU": 15, "R_ELBO": 84, "L_ELBO": -76, "L_SHOU":-40},
    {"R_SHOU": 57, "R_ELBO": 20, "L_ELBO": -80, "L_SHOU":-46},
    {"R_SHOU": 29, "R_ELBO": 92, "L_ELBO": -36, "L_SHOU":-74},
    {"R_SHOU": 75, "R_ELBO": 30, "L_ELBO": -31, "L_SHOU":-79}
]

IDLE_MAPS = [
    {"HEAD_R":5,"R_SHOU":81,"HEAD_P":-1,"R_ELBO":18,"L_ELBO":-15,"HEAD_Y":0,"L_SHOU":-81},
    {"HEAD_R":-7,"R_SHOU":105,"HEAD_P":-3,"R_ELBO":5,"L_ELBO":-5,"HEAD_Y":0,"L_SHOU":-105},
]

HOME_SERVO_MAP = {"HEAD_R":   0, 'HEAD_P': 0, 'HEAD_Y':  0, 'BODY_Y': 0,
                  'L_SHOU': -90, 'L_ELBO': 0, 'R_SHOU': 90, 'R_ELBO': 0}
HOME_LED_MAP = {'L_EYE_R': 255, 'L_EYE_G': 255, 'L_EYE_B': 255, 'R_EYE_R': 255, 'R_EYE_G': 255, 'R_EYE_B': 255}

# MOTION
# motionとは、poseの系列。poseは、各関節の角度指令値(map)と到達時間(msec)の辞書
NOD_MOTION = [
    {"Msec": 1000, "ServoMap":{"R_SHOU":105,"HEAD_P":-15,"R_ELBO":0,"L_ELBO":-3,"L_SHOU":-102}},
    {"Msec": 1000, "ServoMap":{"R_SHOU":77,"HEAD_P":20,"R_ELBO":17,"L_ELBO":-17,"L_SHOU":-79}},
    {"Msec": 1000, "ServoMap":{"R_SHOU":92,"HEAD_P":-5,"R_ELBO":5,"L_ELBO":-7,"L_SHOU":-88}},
]