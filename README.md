# robotcontroller_client
Sample programs for communicating with Sota (CommU).


# Install
```
git clone https://github.com/social-robotics-lab/robotcontroller_client.git
cd robotcontroller_client
docker build -t robotcontroller_client .
```

# Run
```
docker run -it --name robotcontroller_client --mount type=bind,source="$(pwd)"/src,target=/tmp --rm robotcontroller_client /bin/bash
python3 sample.py --host 192.168.x.x 
```


# データ送信・コマンド送信

## Wavデータ

通常のWavファイルをバイナリファイルとして読み込み、そのデータを送信します。RobotControllerでは、そのWavファイルの内容を再生します。Wavデータはデフォルトでは22222ポートに送信します（RobotController側の設定ファイルを変更することによって番号を変えられます）。

## 動作コマンド

JSON形式で記述された各軸への指令値のデータを送信します。RobotControllerではその指令値の通りに軸を動かします。動作コマンドはデフォルトでは22222ポートに送信します。

形式：

    {"msec": duration, "map": {"LABEL": value, ...}}

例：

    {"msec": 1000, "map": {"BODY_Y": 10, "R_SHOU_P": 0}}

- msecは軸の角度が指令値に到達するまでにかかる秒数です。単位はミリ秒で、整数値（int）の値をとります。
- mapは軸のラベル(LABEL)と角度の指令値(value)のマップです。軸のラベルはCommUとSotaで異なります。詳細は[各軸の情報](#各軸の情報)を見てください。valueの単位は度で、整数値（int）の値をとります。
 

## LEDコマンド

LEDコマンドも動作コマンドと同様です。デフォルトでは22222ポートに送信します。


# 通信プロトコル

RobotControllerとの通信は、
1. 4byte (int) で命令（Wavデータ）のバイト数を送信
1. 命令（Wavデータ）そのものを送信
というプロトコルで行われます。
このプロトコルの実装例は、client_io.pyを参照してください。


# 各軸の情報

注意：複数の軸を同時に動かす場合、各軸の稼働範囲内だったとしても、ロボットの部位が衝突することがあります（モーターロック）。例えば、Sotaは肘を内側に曲げた状態で肩を上に回すと、手が頭に当たります。モーターロック状態が長く続くと発煙・発火・火災の原因になるので、モーターロック状態にならないようにしてください。

## CommU

|ID|ラベル|初期値|可動範囲|
|:--|:--|:--|:--|
| 1|BODY_P  |   0|  -15 ~  15|
| 2|BODY_Y  |   0|  -67 ~  67|
| 3|L_SHOU_P|  60| -108 ~ 108|
| 4|L_SHOU_R|   0|  -45 ~  30|
| 5|R_SHOU_P| -60| -108 ~ 108|
| 6|R_SHOU_R|   0|  -30 ~  45|
| 7|HEAD_P  |   0|  -20 ~  25|
| 8|HEAD_R  |   0|  -15 ~  15|
| 9|HEAD_Y  |   0|  -85 ~  85|
|10|EYES_P  |   0|  -22 ~  22|
|11|L_EYE_Y |   0|  -35 ~  20|
|12|R_EYE_Y |   0|  -20 ~  35|
|13|EYELID  |   0|  -65 ~   3|
|14|MOUTH   |   0|   -3 ~  55|

## Sota

|ID|ラベル|初期値|可動範囲|
|:--|:--|:--|:--|
| 1| BODY_Y|   0 | -61 ~  61|
| 2| L_SHOU| -90 |-180 ~  60|
| 3| L_ELBO|   0 | -90 ~  65|
| 4| R_SHOU|  90 | -60 ~ 180|
| 5| R_ELBO|   0 | -65 ~  90|
| 6| HEAD_Y|   0 | -85 ~  85|
| 7| HEAD_P|   0 | -27 ~   5|
| 8| HEAD_R|   0 | -30 ~  30|

# 各LEDの情報

注意：備考で書かれていることは、開発者のテスト時の状況です。

## CommU

|ID|ラベル|初期値|可動範囲|備考
|:--|:--|:--|:--|:--|
|0|PWR_BTN_R|  0| 0 ~ 255||
|1|PWR_BTN_G|  0| 255 ~ 0|0が点灯|
|2|PWR_BTN_B|  0| 0 ~ 255||
|3|BODY_R   |  0| 0 ~ 255|動作せず|
|4|BODY_G   |  0| 0 ~ 255||
|5|BODY_B   |  0| 0 ~ 255||
|6|L_CHEEK  |  0| 0 ~ 255|両方の頬が点灯|
|7|R_CHEEK  |  0| 0 ~ 255|動作せず|

## Sota

|ID|ラベル|初期値|可動範囲|備考
|:--|:--|:--|:--|:--|
| 0|PWR_BTN_R|   0| 0 ~ 255||
| 1|PWR_BTN_G|   0| 255 ~ 0|0が点灯|
| 2|PWR_BTN_B|   0| 0 ~ 255||
| 8|R_EYE_R  | 180| 0 ~ 255||
| 9|R_EYE_G  |  80| 0 ~ 255||
|10|R_EYE_B  |   0| 0 ~ 255||
|11|L_EYE_R  | 180| 0 ~ 255||
|12|L_EYE_G  |  80| 0 ~ 255||
|13|L_EYE_B  |   0| 0 ~ 255||
|14|MOUTH    |   0| 0 ~ 255|動作せず|
