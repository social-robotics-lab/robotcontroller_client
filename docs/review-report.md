# 実機受入前のコードレビューと修正記録

開始ブランチは`feature/python-client-redesign`、HEADは`68d457e484e25e10024930adf921d13f768df781`。作業ツリーはcleanで、既存変更の上書きはない。公開APIと現在の設計を維持した。

## 発見した問題と対応

| 問題 | 対応・回帰検証 |
|---|---|
| READMEのsample.wavがルートに存在しない | assets/sample.wavへ統一。02/05は省略時にスクリプト位置を基準に同梱WAVを利用する |
| 旧WAVは44.1kHz/16bit/ステレオで新型非対応 | 標準ライブラリで生成した24kHz/16bit/mono、0.25秒の正弦波へ置換。形式と再生成一致をテスト |
| 旧WAVの制作元・固有の再配布条件を確認できない | 2021年の追加・更新履歴、MIT LICENSE、リポジトリ内資料を確認したが音源の出所は特定できず。外部素材を使わない生成WAVに置き換え、assets/README.mdにMIT適用を明示。旧バイナリは現行ツリーから削除し履歴は保持 |
| send_pcmを続けて呼ぶと毎回基準時刻と送信バイト数がリセットされ、先送りできる | 同じSTART内で基準と送信量を継続。START成功時にリセット。仮想時計で別呼び出しの送信時刻0/20/40msを確認 |
| ソケット取得後の設定がKeyboardInterrupt等で中断された際、コンストラクタがcloseしない | 初期化中のOSError以外の例外でも解放して再送出。モックの設定中断でcloseを確認 |
| READMEで推奨版・実行確認版が明瞭でない | Python 3.12を推奨し、実測結果と未確認版を分離。clone、venvのPython指定、形式、移行手順を照合・補足 |

## 問題が確認されなかった項目と根拠

- ストリーム状態管理: [Javaサーバーmain](https://github.com/social-robotics-lab/RobotController/tree/384686a7d68dadef338d6188f21441c653af135a)のREADMEとtools/phase_g_audio_client.pyを再取得・照合。CONNECTION_READY後START、STARTED後DATA、END後ENDED、CANCEL後CANCELLEDの順序を保持。絶対バイトスケジュール、既定prebuffer=0/catchup=0相当、1チャンク超の遅延時rebaseも保持した。
- Playback: AudioStreamを生成・操作・解放するのはワーカーのみ。waitはEventとjoin、cancel/closeはキャンセルEventとwaitだけでソケットを読まない。6本の呼び出し側でwait/cancel/closeを競合させ、全Connectionのsend/receive/readable/closeの実行スレッドがワーカー1本であることを記録して確認した。
- 同時呼び出しの完了伝播: CANCELLED、AUDIO_ERROR、応答タイムアウト、切断、誤ったSTATUSの5ケースで、6本全てへ同一の結果または適切な例外型が伝わる。終了後のワーカー停止とTCP EOFを確認。END選択後のcancelではCANCELを重ねずENDEDを返すことも確認した。STATUS/ERRORの競合読み取りやデッドロックは確認されなかった。
- TCP: sendall、ヘッダ/本文の部分受信、64MiB上限、ゼロ/負相当/過大フレーム長、フレーム全体の受信期限、送信タイムアウト、EOF、JSON異常を既存テストで確認した。
- WAV/errors: 対応形式・空データ・切れたPCMを拒否し、例外を呼び出し元に返す。CommunicationTimeoutはCommunicationErrorとTimeoutErrorの双方で捕捉できる。サーバーERRORコードはServerError.code/nameに保持される。追加の設計変更は不要と判断した。
- API: 従来9コマンドの送信形式をモックで確認。play_wav/play_pose/play_motionの戻り値はミリ秒、stream_wavはPlaybackを維持。従来コマンドの送信成功を再生完了とは説明していない。RobotToolsの秒単位からの移行説明、optional dependenciesのgtts/azureとREADMEの指定が一致する。

## コマンド・音声の検証

tests/test_assets.pyでREADMEから02/05の実行例を抽出し、IP/portと実行前確認のみテスト用に差し替えてmainを実行した。実際のクライアントからループバックのモックサーバーへ送り、従来はWAV全体、新型はヘッダなしPCMが一致することを確認した。

実行場所はルート/別フォルダ、WAV指定はREADMEのassets/sample.wav/引数省略の計8ケース。独自の相対パスは通常のカレントディレクトリ基準のまま。同梱assetsパスのみ、カレントディレクトリに存在しなければリポジトリ基準にも対応する。ライブラリのパス解釈は変更していない。

gTTS/Azureは前回同様モックのみ。--help、認証情報未設定、ffmpegの変換引数、AzureのRiff24Khz16BitMonoPcmとaudio_config=Noneをテストした。クラウドSDKは基本依存に追加していない。

## Python版別結果

pyproject.tomlのrequires-pythonは`>=3.10`を維持。環境確認はWindowsのpy -0pで実施し、追加版のダウンロードはしていない。

| Python | 実行検証 |
|---|---|
| 3.10 | インストールなし、実行未確認。前回の構文検証を実行確認とは扱わない |
| 3.11 | インストールなし、実行未確認 |
| 3.12.10 | 変更前118 passed、変更後**135 passed**（3.72秒） |
| 3.13 | インストールなし、実行未確認 |
| 3.14.3 | 既存インストールから専用venvを作成、**135 passed**（3.74秒） |

3.12.10と3.14.3の両方で次を実行し、全て合格した。テストは各版の仮想環境に編集可能インストールしたパッケージを使った。

```sh
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m compileall -q robotcontroller examples tests assets
python -m pip check
```

135件には新規17件を含む。ruffは26ファイルの整形を確認。pip checkは不整合なし。

## 変更ファイル

追加: assets/README.md、assets/generate_sample.py、assets/sample.wav、tests/test_assets.py、docs/review-report.md。

変更: README.md、examples/_common.py、examples/02_play_wav.py、examples/05_audio_stream.py、robotcontroller/audio_stream.py、robotcontroller/protocol.py、tests/test_audio_stream.py、tests/test_protocol.py、docs/implementation-report.md。

削除: src/sample.wav。client.py、wav.py、errors.py、公開APIとpyproject.tomlの対応範囲は変更していない。

## 未検証・残る制限・実機受入

Sotaへの接続・制御・音声再生・SSH・転送・デプロイ・実サーバー起動停止は一切していない。クラウド音声合成、macOS、Python 3.10/3.11/3.13の実行も未実施。

AudioStreamの直接のスレッド共有は対象外で、Playbackを利用する。ENDによる終了処理が選択済みならcancelはENDED待ちとなるため、戻り値の確認が必要。通信のタイムアウトは各操作の期限であり、再生全体の制限時間ではない。WAVはメモリへ読み込む現設計を維持した。

実機受入で重点確認するのは、生成テスト音の音量、新型START/ENDと口LED同期、CANCELLED後の別音声再生、同一接続の連続再生、切断時の接続枠解放、BUSY、長時間の音切れ/ALSA XRUN。従来の停止は安全停止の保証ではなく、実機の周辺・初期姿勢・停止手段を操作者が確認する。自動テスト合格を実機合格とは扱わない。
