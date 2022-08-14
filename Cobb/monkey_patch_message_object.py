from Cobb.utils.startup_helpers import monkeypatch
from pyrogram.types import Message

@monkeypatch(Message)
class MSG():
    def __init__(self, *args, **kwargs) -> None:
        super.__init__(*args, **kwargs)
    
    @property
    def input_str(self):
        msg = self.text
        if not msg:
            return None
        if " " in msg:
            return msg[msg.find(" ") + 1 :]
    