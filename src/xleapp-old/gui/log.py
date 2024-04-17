import logging

from xleapp import gui


buffer: str = ""


class Handler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.setLevel(logging.INFO)

    def emit(self, record):
        global buffer
        record = f"{record.name}, [{record.levelname}], {record.msg}"
        buffer = f"{buffer}\n{record}".strip()
        gui.window["<LOG>"].update(value=buffer)
