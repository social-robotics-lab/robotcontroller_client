# Pythonクライアント再設計 実装報告

実施日: 2026-11-13。作業ブランチ: `feature/python-client-redesign`。
開始HEAD: `a9914914e725fbb1daadad225e5990a1ef6fc570`。開始時の作業ツリーはclean。
最終HEADは本報告を含むPhase 5コミット（最終チャットにハッシュを記載）。

## 実装した機能

- 接続先・ポート・タイムアウト・機種検証設定を保持するRobotController。
- 従来9コマンドのフレーム互換。read_axesだけ応答を読み、他はACKを待たない。
- sendall、部分受信、切断検出、受信フレーム全体の期限、不正長とJSONの検証、例外時の解放。
- audio_stream_v1のCONNECTION_READY/STARTED/ENDED/CANCELLEDバリアと状態検証。
- 最大960バイトのPCM、48,000 bytes/secの絶対スケジュール、遅延時rebase、DATA中の応答監視。
- 同期完了待ち、バックグラウンドPlayback、キャンセル、同一接続での連続再生。
- 24kHz・mono・16bit PCM WAV検証とPCM抽出。自動形式変換は追加していない。
- Sota可動範囲・LED値・姿勢構造・速度の入力検証。リセットと独立したビート生成。
- 日本語README、短い7サンプル、独立したgTTS/ffmpeg・Azure Speechの例。

## ファイル

追加:

- `robotcontroller/__init__.py`, `client.py`, `protocol.py`, `audio_stream.py`, `errors.py`, `wav.py`, `helpers.py`
- `pyproject.toml`
- `examples/01_read_axes.py`〜`07_azure_tts.py`, `examples/_common.py`
- `tests/conftest.py`, `test_protocol.py`, `test_client.py`, `test_audio_stream.py`, `test_examples.py`
- `docs/design.md`, `docs/implementation-report.md`

変更: `README.md`, `.gitignore`。

削除: `Dockerfile`, `src/serverio.py`, `src/client.py`, `src/sample.py`, `src/jtalk.py`。

既存の`LICENSE`と`src/sample.wav`は保持。参照用RobotController/robo-tutorialは変更していない。

## 公開API

`from robotcontroller import RobotController`

RobotController:
`read_axes`, `play_wav`, `stop_wav`, `play_pose`, `stop_pose`, `play_motion`, `stop_motion`,
`play_idle_motion`, `stop_idle_motion`, `reset_pose`, `stream_wav`, `audio_stream`。

AudioStream: `start`, `send_pcm`, `end`, `cancel`, `stream_wav`, `close`、with構文。

Playback: `wait`, `cancel`, `close`, `done`, `result`、with構文。

独立ヘルパー: `robotcontroller.helpers.make_beat_motion(duration_seconds, speed=1.0)`。

例外: `RobotControllerError`, `CommunicationError`, `CommunicationTimeout`, `ProtocolError`, `ServerError`。

## 移行の要点

IP・ポートを各関数に渡す方式からインスタンスへ変更した。通信プロトコルの互換を保持し、旧importの互換層は設けていない。play_wav/play_pose/play_motionの戻り値はミリ秒で統一した（RobotToolsのWAV・発話の秒とは異なる）。従来の送信成功・予定時間を完了通知とは扱わない。

OpenJTalk/say_textは外し、TTSはサンプルへ分離。旧モーションの範囲外角度をコピーせず、ビート生成は頭の小さい左右動作に変更。Sota検証は既定で有効。他機種はmodel=Noneと操作者の範囲確認が必要。

## テスト結果

Windows / CPython 3.12で以下を実施した。

| 検証 | 結果 |
|---|---|
| 編集可能インストール `pip install -e '.[test]'` | 成功 |
| `pytest -q` | **118 passed**（2.01秒） |
| `ruff check .` | 合格 |
| `ruff format --check .` | 合格 |
| `compileall -q robotcontroller examples tests` | 合格 |
| `pip check` | 依存関係の不整合なし |
| `pip wheel . --no-deps --wheel-dir dist` | wheel生成成功 |
| `python -I`でwheel内から直接import | 成功、gTTS/Azureのimportなし、接続なし |
| Python 3.10の文法でAST解析 | Pythonソース20ファイル合格 |

テストはTCPフレーム、2MiB送信、sendall、分割ヘッダ/本文、異常長、EOF、接続/送信/受信タイムアウト、JSON、従来9コマンド、入力検証、WAV破損・形式、START/END/CANCEL、ENDED待ち、連続再生、中止後再開、全エラーコード、不正状態、仮想時計のペーシング/rebaseを含む。サーバー応答を意図的に遅らせ、各バリア前に次のレコードが送信されないことも確認した。

gTTS・Azureはモックのみ。7サンプルのimport/--help、認証情報不在、MP3変換引数、Azureの出力形式・PCスピーカー無効設定を確認した。テスト全体でsocket.connectを127.0.0.1に限定している。

## 未実施・制限と後工程

実際のSotaへの接続・制御・音声再生・転送・デプロイ・サーバー起動停止は一切実施していない。クラウド音声合成、macOS、Python 3.10/3.11/3.13以降での実行試験も未実施。Python 3.10は構文検証のみ。WAVの自動変換とリアルタイムTTSは今回の範囲外。

実機受入は操作者が安全を確認して手動で行う。順序は、read_axes、控えめな姿勢・モーション、従来WAVと停止、アイドルと停止、新型WAVのENDED、中止とCANCELLED、連続再生、切断時の接続枠解放。停止が物理的な即時停止を保証しないことを確認する。長時間音声ではサーバー側の既知のALSA XRUN/音切れも別途観測する。

利用開始はREADMEの仮想環境作成・`pip install -e .`・`examples/01_read_axes.py --host <IP>`を参照。次の作業はmacOS/対応Python版での検証と操作者による実機受入。

## Git操作

指定ブランチを作成し、Phaseごとの5コミットに分けた。mainへの直接コミット・マージ、履歴改変、force pushはしていない。push・Pull Request作成は未実施。PyPI公開も未実施。
