"""利用側で捕捉できる通信・プロトコル例外。"""


class RobotControllerError(Exception):
    """クライアントの通信エラーの基底クラス。"""


class CommunicationError(RobotControllerError):
    """接続失敗、切断、送受信失敗。"""


class CommunicationTimeout(CommunicationError, TimeoutError):
    """通信の制限時間を超えた。動作完了は未確認。"""


class ProtocolError(RobotControllerError):
    """フレーム、JSON、状態遷移が不正。"""


class ServerError(RobotControllerError):
    """サーバーが返したERROR。"""

    def __init__(self, code):
        self.code = code
        self.name = {1: "BUSY", 2: "PROTOCOL_ERROR", 3: "AUDIO_ERROR",
                     4: "QUEUE_OVERFLOW"}.get(code, "UNKNOWN_ERROR")
        super().__init__(f"サーバーエラー: {self.name} (0x{code:02X})。再生完了は未確認です。")
