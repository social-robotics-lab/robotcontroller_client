# robotcontroller-client

SotaなどをPythonから操作する研究室向けクライアントです。基本機能はPython標準ライブラリだけで動き、Docker・OpenJTalkは不要です。Python 3.10以上、Windows/macOSを対象とします。今回の自動検証はWindowsのローカル環境のみで、実機・macOSでの動作は未検証です。

ロボット側には[RobotController](https://github.com/social-robotics-lab/RobotController)が必要です。サーバーのインストールと起動手順は本体READMEを参照してください。[授業用robo-tutorial](https://github.com/social-robotics-lab/robo-tutorial)は別管理です。

## インストールと最初の実行

ソースを取得し、リポジトリのフォルダで実行します。PyPIには公開していません。

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe examples/01_read_axes.py --host 192.168.11.7 --port 22222
```

macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python examples/01_read_axes.py --host 192.168.11.7 --port 22222
```

以下の`python`は仮想環境の実行ファイルに読み替えてください。activateした場合は`python`で実行できます。IPは操作者が確認したロボットのIPに置き換えます。ポート初期値は22222、通信タイムアウトは秒（既定10秒）です。最初の例は角度の読み取りだけです。

```python
from robotcontroller import RobotController

robot = RobotController("192.168.11.7", port=22222, timeout=10)
print(robot.read_axes())  # 軸名→角度（度）
robot.play_pose({"Msec": 1000, "ServoMap": {"HEAD_Y": 3}})
```

importとインスタンス生成だけでは接続しません。既定`model="Sota"`はサーボ名・可動範囲・LED名を検証します。CommU等は`model=None`を明示し、機種別の軸名・範囲を[サーバー実装](https://github.com/social-robotics-lab/RobotController/tree/main/src/servo)と照合してください。Noneでは機種別の検証は行いません。

## 操作API

| メソッド | 引数・戻り値 |
|---|---|
| `read_axes()` | 整数の角度（度）の辞書 |
| `play_wav(path)` | PCM WAV全体を送信。ファイル長の整数ミリ秒を返す |
| `stop_wav()` | 従来WAVの停止要求。None |
| `play_pose(pose)` | `Msec`と`ServoMap`/`LedMap`。予定ミリ秒を返す |
| `stop_pose()` | 姿勢の停止要求。None |
| `play_motion(motion)` | 姿勢のリスト。Msecの合計を返す |
| `stop_motion()` | モーション停止要求。None |
| `play_idle_motion(speed=1.0, pause=1000)` | Pauseはミリ秒。None |
| `stop_idle_motion()` | アイドル停止要求。None |
| `reset_pose(speed=1.0)` | Sota専用ホーム姿勢と白色眼LED。予定ミリ秒を返す |
| `stream_wav(path, wait=True)` | 新型方式。Playbackを返す。既定はENDEDまで待つ |
| `audio_stream()` | 同一TCP接続で複数音声を順次処理するAudioStream |

従来9コマンドは1コマンド1接続、コマンドとペイロードを別の4バイトbig-endian長フレームで送ります。`read_axes`以外は成功・失敗・完了の返信がありません。戻り値の時間と送信成功は実際の動作完了を保証しません。クライアント側の最大本文長は64MiBです。

`Msec`と`Pause`は非負の整数、Speedは正の有限数で、動作時間`1000 / Speed`が1〜2147483647msになる値です。ServoMapは整数角度、LedMapは0〜255の整数です。

停止コマンドは安全停止の保証ではありません。サーバーのstop_poseは現在角度の100ms姿勢を投入する旧処理で、stop_motion等も物理的な即時停止を保証しません。stop_wavは他のaplayにも影響し得ます。新型音声には使いません。

## 従来WAVと新型ストリーミング

従来play_wavはWAVコンテナ全体を送り、サーバー側aplayが再生します。クライアントはPCM WAVを受け付け、実際に再生できる形式はサーバー環境に依存します。

新型audio_stream_v1は24,000Hz・16bit・モノラル・非圧縮PCM WAVのみ受け付けます。WAVヘッダを除いたsigned little-endian PCMを最大960バイトずつ48,000 bytes/sec基準で送ります。自動リサンプリングはしません。CONNECTION_READY→STARTEDを確認してからDATAを送信し、DATA中も応答を監視します。END後のENDEDはサーバーのdrain/close完了であり、マイクによる音響測定ではありません。[現行の通信仕様](https://github.com/social-robotics-lab/RobotController#通信プロトコル)に準拠しています。

```python
robot.stream_wav("sample.wav", wait=True)  # ENDEDを確認して戻る

# 同一接続。各ENDEDを待ってから次のSTARTを送る。
with robot.audio_stream() as stream:
    stream.stream_wav("first.wav")
    stream.stream_wav("second.wav")

# バックグラウンド送信。必ずwait/cancel/closeまたはwithで回収する。
with robot.stream_wav("sample.wav", wait=False) as playback:
    print(playback.wait())  # "ENDED"、中止完了なら"CANCELLED"
```

Playback.cancel()はCANCELを要求しCANCELLEDまで待ちます。END送信後ならENDEDを待つので戻り値を確認してください。cancel/closeは通信タイムアウトまで待つ場合があります。doneとresultで確認でき、未完了resultはNone、失敗なら例外です。Playbackは専用スレッドを持ちます。複数音声は前のwaitを完了してから開始してください。サーバーの音声接続枠は1つで、待機中AudioStreamも枠を保持します。

低水準APIは`AudioStream.start()`→`send_pcm(bytes)`→`end()`または`cancel()`です。raw PCMのメタデータは検出できないので、24kHz/mono/S16_LEは呼び出し側で保証します。AudioStreamはスレッド間で共有しないでください。closeだけでは正常終了・中止完了は未確認です。エラー時は接続を閉じます。QUEUE_OVERFLOWも例外にし、自動再試行しません。

## サンプルと実機操作の安全

すべて--hostが必須、--portと--timeoutも指定可能です。--helpで引数を確認できます。読み取り以外はyesの手動入力後に動作します。

```sh
python examples/01_read_axes.py --host 192.168.11.7
python examples/02_play_wav.py --host 192.168.11.7 sample.wav
python examples/03_play_pose.py --host 192.168.11.7
python examples/04_play_motion.py --host 192.168.11.7
python examples/05_audio_stream.py --host 192.168.11.7 sample.wav
```

03/04はSotaのHEAD_Yを±3度でゆっくり動かします。範囲内でも部位同士が衝突する場合があります。現在の姿勢・周辺空間・配線・転倒防止・停止手順を確認してから操作者が手動実行してください。reset_poseやアイドル動作は腕も動きます。モーターロックは発熱・発煙の原因になります。

## 音声合成（任意）

基本インストールにクラウドSDKは含みません。入力テキストは外部サービスへ送信されます。

gTTSは[MP3を出力](https://gtts.readthedocs.io/en/latest/)します。変換用に[ffmpeg](https://ffmpeg.org/download.html)を別途インストールしPATHに追加してください。Windowsは配布元のWindowsビルド、macOSでHomebrewを利用していれば`brew install ffmpeg`が選択肢です。サンプルは24kHz/mono/pcm_s16le WAVへ変換します。pydubは不要です。

```sh
python -m pip install -e ".[gtts]"
python examples/06_gtts.py --host 192.168.11.7 "こんにちは"
```

Azureは[公式の合成API](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-speech-synthesis?pivots=programming-language-python)でRiff24Khz16BitMonoPcmを指定します。WAVのPCMをそのままストリームに利用でき、ffmpegは不要です。PCのスピーカー出力は無効にします。

```sh
python -m pip install -e ".[azure]"
```

Windows PowerShell:

```powershell
$env:SPEECH_KEY = Read-Host "Azure Speechキー"
$env:SPEECH_REGION = "japanwest"
python examples/07_azure_tts.py --host 192.168.11.7 "こんにちは"
```

macOS:

```sh
read -s SPEECH_KEY
export SPEECH_KEY
export SPEECH_REGION=japanwest
python examples/07_azure_tts.py --host 192.168.11.7 "こんにちは"
```

キーと実際のリソースのリージョンを設定します。キーをコード・Git・ログに記録しないでください。SDK対応OS/Python版は公式資料で確認してください。認証情報のない環境で合成APIは実行していません。

## よくあるエラー

| エラー | 対処 |
|---|---|
| CommunicationError / 接続拒否 | IP、ポート、ネットワーク、ファイアウォール、操作者が起動したサーバーを確認 |
| CommunicationTimeout | 通信断・サーバー応答・timeout秒を確認。完了とは扱わない |
| BUSY | 別クライアントや待機中AudioStreamによる接続枠の保持を確認 |
| PROTOCOL_ERROR / ProtocolError | サーバーの版、応答、呼び出し順を確認 |
| AUDIO_ERROR | サーバーログ、JNI/ALSAを操作者が確認 |
| QUEUE_OVERFLOW | 送信速度、ネットワーク、サーバー負荷を確認。音声は中止されている |
| ValueError（WAV） | 24kHz/16bit/mono PCM WAVか、破損がないか確認 |
| ValueError（姿勢） | Msec、軸名、機種、整数角度・可動範囲を確認 |
| ModuleNotFoundError | 同じPythonでpip install -e .を実行したか確認 |

RobotControllerErrorで通信・プロトコル・サーバーエラーをまとめて捕捉できます。引数・ファイル不正はValueError/OSErrorです。サーバー受入記録には長時間のまれなALSA XRUN/音切れの未解決事項があります。クライアントのテスト合格はその解消を意味しません。

## 旧APIからの移行

- `client.play_pose(ip, port, pose)` → `RobotController(ip, port).play_pose(pose)`。RobotToolsもクラス名とimportを変更します。JSONキーはREADME旧版のmsec/mapではなくMsec/ServoMap/LedMapです。
- 旧clientのplay_wav/play_pose/play_motionと新APIはミリ秒を返します。RobotTools.play_wav/say_textの**秒**とは異なります。RobotToolsのplay_pose/play_motionはNoneでしたが、新版は予定ミリ秒です。
- reset_poseはSota専用として維持。say_text/OpenJTalkは廃止し、06/07の独立サンプルへ分離しました。
- `make_speech_motion(duration_ms)` / `RobotTools.make_beat_motion(duration_seconds)` は`from robotcontroller.helpers import make_beat_motion`へ移行します。引数は**秒**です。旧腕振りをコピーせず控えめなHEAD_Y動作とし、最後に中央へ戻す1000msを追加します。
- 旧srcとDockerfileを削除しました。旧コードはGit履歴から参照できます。関数形式の自動互換層はありません。範囲外値・未知キーを送信前に拒否するため、以前サーバー側で丸められた値も修正が必要です。

## 開発と検証

```sh
python -m pip install -e ".[test]"
python -m pytest -q
python -m ruff check .
python -m compileall -q robotcontroller examples tests
```

テストはループバック・モック・仮想時計のみを使います。ロボット・クラウドAPI・実サーバー起動は不要です。[設計記録](docs/design.md)に調査根拠を記載しています。実機受入は未実施で、操作者による後工程です。読み取り、従来9コマンド、新型の完了・中止・連続再生、長時間音声、切断時の枠解放を安全な実機環境で確認してください。
