import logging

import xleapp.gui as gui


buffer: str = ""


class Handler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.setLevel(logging.INFO)

    def emit(self, record):
        global buffer
        record = f"{record.name}, [{record.levelname}], {record.message}"
        buffer = f"{buffer}\n{record}".strip()
        gui.window["-LOG-"].update(value=buffer)
