import codecs
import csv
from pathlib import Path
from typing import Union

from xleapp import globals as g


class TsvManager:
    connection: codecs = None
    report_folder: Path = None
    file: Path = None

    def __init__(self, file: Union[Path, str]):
        self.report_folder = Path(g.report_folder) / "_TSV Exports"
        self.report_folder.mkdir(parents=True, exist_ok=True)
        if isinstance(file, Path):
            self.file = self.file
        else:
            self.file = self.report_folder / f"{file}.tsv"

    def __enter__(self):
        self.connection = codecs.open(self.file, "a", 'utf-8-sig')
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


def save(data_headers, data_list, tsvname):

    with TsvManager(tsvname) as file:
        tsv_writer = csv.writer(file, delimiter="\t")
        tsv_writer.writerow(data_headers)
        for i in data_list:
            tsv_writer.writerow(i)
