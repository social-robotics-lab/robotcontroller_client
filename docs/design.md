# 調査・設計記録（2026-11-13）

開始時: main / a9914914e725fbb1daadad225e5990a1ef6fc570、作業ツリー clean。
作業先: feature/python-client-redesign。参照リポジトリは読み取りのみ。

## 根拠

- [RobotController main](https://github.com/social-robotics-lab/RobotController/tree/384686a7d68dadef338d6188f21441c653af135a) のREADME、src/main/TCPServer.java、tools/phase_g_audio_client.py、test/main/AudioStreamingProtocolTest.javaをGitHubから確認。
- ローカル参照のtools/test_phase_g_audio_client.py、ServoConverter_Sota.java、docs/phase-g-result-2026-09-16.mdも確認。サーバーmainの親はローカルmain c6dbfdae68b62f9cb1b834b95492b5afa7df16a1。最新コミットの変更はREADMEのリリースリンク。
- [robo-tutorial](https://github.com/social-robotics-lab/robo-tutorial) のtutorial_01/robottools.pyをGitHubとローカルで確認。tutorial_01〜03/sample.pyをローカルHEAD 196a2cdd9fe926ee3647fbbc1b83fc510fafc0d2で確認。
- 本リポジトリのsrc/serverio.py、client.py、sample.py、jtalk.py、Dockerfile、README.mdを確認。

## 決定

通信互換を保持するが旧関数APIの自動互換層は導入しない。RobotControllerは接続設定を保持し、従来コマンドごとに接続する。JSONはensure_ascii=Trueとしてサーバーの既定charset依存を避ける。従来の所要時間の戻り値はミリ秒に統一し、完了通知とは区別する。

protocolは長さ検証・sendall・完全受信・フレーム全体の受信期限・例外変換を担当。clientは9コマンドと引数検証を担当。Sotaを既定の検証対象とし、他機種はmodel=Noneと明示し、軸名と範囲を操作者が確認する。

AudioStreamは同期型の永続接続を提供する。START/END/CANCELの応答を厳密に検証し、DATA中はselectで応答を監視する。受入クライアントの既定値（prebuffer=0、catchup=0）、絶対バイトスケジュール、1チャンクを超える遅れのrebaseを保持する。実験用prebuffer/catchupオプションは公開しない。高水準stream_wav(wait=False)は専用スレッドのPlaybackを返し、wait/cancel/closeで回収可能とする。

reset_poseはSota専用メソッドとして継承する。旧ランダム腕振りにはR_ELBO=92（範囲上限90）、旧うなずきにはHEAD_P=20（上限5）があるためコピーしない。ビート生成は通信しないhelpers.make_beat_motionに分離し、控えめな頭の左右動作で例示する。OpenJTalk/say_textは廃止し、gTTS/Azureを独立サンプルにする。

受入記録ではSTART/END/CANCEL、再開始、BUSY、切断後解放は合格。ただし長時間のALSA XRUN/音切れは未解決。本クライアントの実機試験は行わず、ローカル単体・ループバックテストのみを実施する。
