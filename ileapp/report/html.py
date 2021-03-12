import importlib
import shutil
from pathlib import Path

import ileapp.report.templating as templating


def copy_static_files(report_folder):
    html_report_root = Path(importlib.util.find_spec(__name__).origin).parent
    static_folder = html_report_root / '_static'
    logo = html_report_root.parent.parent / 'logo.jpg'

    report_folder = report_folder / '_static'

    shutil.copytree(static_folder, report_folder)
    shutil.copy(logo, static_folder)


def generate_index(report_folder: Path,
                   log_folder: Path,
                   extraction_type: str,
                   processing_time: float) -> None:
    index_html = templating.Index(report_folder,
                                  log_folder,
                                  extraction_type,
                                  processing_time).html()
    index_file = report_folder / 'index.html'
    index_file.write_text(index_html)
