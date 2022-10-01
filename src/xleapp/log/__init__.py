import importlib.util
import logging
import logging.config
import os
import typing as t

from pathlib import Path

import xleapp.globals as g
import yaml

from xleapp.helpers.utils import generate_program_header


StrPath = t.Union[str, os.PathLike[str]]


class ProcessFileFilter(logging.Filter):
    def filter(self, record):
        return record.name == "xleapp.process" and record.levelno >= 20


class InfoLogFileFilter(logging.Filter):
    def filter(self, record):
        return record.name == "xleapp.logfile" and record.levelno >= 20


class DebugFileFilter(logging.Filter):
    def filter(self, record):
        return g.app.debug


class StreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord):
        if record.msg.startswith("->"):
            record.msg = f"    {record.msg}"
        logging.StreamHandler.emit(self, record)


class FileHandler(logging.FileHandler):
    def __init__(
        self,
        filename: StrPath,
        mode: str = "a",
        encoding: t.Union[str, None] = None,
        delay: bool = False,
        errors: t.Union[str, None] = None,
    ) -> None:
        super().__init__(
            filename,
            mode=mode,
            encoding=encoding,
            delay=delay,
            errors=errors,
        )

    def emit(self, record: logging.LogRecord):
        if record.msg.startswith("->"):
            record.msg = f"    {record.msg}"
        logging.FileHandler.emit(self, record)


class FileHandlerWithHeader(logging.FileHandler):
    def __init__(self, filename, header, mode="a", encoding=None, delay=0):
        self.header = header
        self.file_pre_exists = Path(filename)
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
        if not delay and self.stream is not None:
            self.stream.write("%s\n" % header)

    def emit(self, record: logging.LogRecord):
        if self.stream is None:
            self.stream = self._open()
            if not self.file_pre_exists:
                self.stream.write("%s\n" % self.header)

        message = record.msg
        if message.startswith("->"):
            message = f"    {message}"
        record.msg = message
        logging.FileHandler.emit(self, record)


def init() -> None:
    mod = importlib.util.find_spec(__name__)

    if not mod:
        raise FileNotFoundError("Missing package 'log_config.yaml' to configure logging!")

    if mod.origin:
        log_config = Path(mod.origin).parent / "log_config.yaml"
        with open(log_config) as file:
            config = yaml.safe_load(file.read())

        if not g.app.log_folder.exists():
            g.app.log_folder.mkdir(parents=True, exist_ok=True)

        info_log_file = config["handlers"]["info_file_handler"]["filename"]
        config["handlers"]["info_file_handler"]["filename"] = (
            g.app.log_folder / info_log_file
        )
        config["handlers"]["info_file_handler"]["header"] = generate_program_header(
            project_version=f"{g.app.project} v{g.app.version}",
            input_path=g.app.input_path,
            output_path=g.app.output_path,
            num_to_process=g.app.num_to_process,
            num_of_categories=g.app.num_of_categories,
        )

        process_log_file = config["handlers"]["process_file_handler"]["filename"]
        config["handlers"]["process_file_handler"]["filename"] = (
            g.app.log_folder / process_log_file
        )

        debug_log_file = config["handlers"]["debug_file_handler"]["filename"]
        config["handlers"]["debug_file_handler"]["filename"] = (
            g.app.log_folder / debug_log_file
        )

        logging.config.dictConfig(config)
    else:
        raise FileNotFoundError(
            "Package found! Missing 'log_config.yaml' to "
            "configure logging! Reinstall package.",
        )
