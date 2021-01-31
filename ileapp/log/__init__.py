import importlib
import logging
import logging.config
from pathlib import Path

import ileapp.globals as props
import yaml


class LoggingContext(object):
    def __init__(self, logger, level=None, handler=None, close=True):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()


class FileHandlerWithHeader(logging.FileHandler):
    def __init__(self, filename, header, mode='a', encoding=None, delay=0):
        self.header = header
        self.file_pre_exists = Path(filename)
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
        if not delay and self.stream is not None:
            self.stream.write('%s\n' % header)

    def emit(self, record):
        if self.stream is None:
            self.stream = self._open()
            if not self.file_pre_exists:
                self.stream.write('%s\n' % self.header)
        logging.FileHandler.emit(self, record)


logConfig = Path(importlib.util.find_spec(__name__).origin).parent / 'log_config.yaml'
with open(logConfig, 'r') as file:
    config = yaml.safe_load(file.read())

log_folder = Path(props.props.run_time_info['report_folder_base']) / 'Script Logs'
if not log_folder.exists():
    log_folder.mkdir(parents=True, exist_ok=True)

log_file = config['handlers']['info_file_handler']['filename']
config['handlers']['info_file_handler']['filename'] = log_folder / log_file

logging.config.dictConfig(config)
