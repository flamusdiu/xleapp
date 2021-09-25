import codecs
import csv
from pathlib import Path


def save(report_folder: Path, data_headers, data_list, tsvname):
    tsv_report_folder = report_folder / "_TSV Exports"

    tsv_report_folder.mkdir(parents=True, exist_ok=True)
    tsv_file = tsv_report_folder / f"{tsvname}.tsv"
    with codecs.open(tsv_file, "a", "utf-8-sig") as f:
        tsv_writer = csv.writer(f, delimiter="\t")
        tsv_writer.writerow(data_headers)
        for i in data_list:
            tsv_writer.writerow(i)
