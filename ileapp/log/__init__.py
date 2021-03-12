import importlib
import logging
import logging.config
from pathlib import Path

import yaml
from ileapp import __authors__, __project__, __version__
import ileapp.globals as g


class Filter:
    def __init__(self, flow):
        self.flow = flow

    def filter(self, record):
        if record.flow == self.flow:
            return True


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


def init_logging(log_folder, input_path, num_to_process, num_of_cateorgies):
    logConfig = Path(importlib.util.find_spec(__name__).origin).parent / 'log_config.yaml'
    with open(logConfig, 'r') as file:
        config = yaml.safe_load(file.read())

    if not log_folder.exists():
        log_folder.mkdir(parents=True, exist_ok=True)

    info_log_file = config['handlers']['info_file_handler']['filename']
    config['handlers']['info_file_handler']['filename'] = log_folder / info_log_file
    config['handlers']['info_file_handler']['header'] = (
        g.generate_program_header(input_path,
                                  num_to_process, num_of_cateorgies)
    )

    process_log_file = config['handlers']['process_file_handler']['filename']
    config['handlers']['process_file_handler']['filename'] = log_folder / process_log_file

    logging.config.dictConfig(config)
