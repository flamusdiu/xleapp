# -*- coding: utf-8 -*-
"""
Reports Module
"""

import importlib
import shutil
from pathlib import Path

from ._db import KmlDBManager, TimelineDBManager, TsvManager
from ._webicons import Icon as WebIcon


def save_to_db(report_folder: Path, db_type: str, **options) -> None:
    if db_type in ["kml", "timeline", "tsv"] and getattr(options, "data_list", []):
        if db_type == "kml":
            db = KmlDBManager(report_folder=report_folder, **options)
        if db_type == "tsv":
            db = TsvManager(report_folder=report_folder, **options)
        if db_type == "timeline":
            db = TimelineDBManager(report_folder=report_folder, **options)

        db.save()


def copy_static_files(report_folder: Path) -> None:
    """Copies static files to report folder.

    Returns:
        None
    """
    html_report_root = Path(importlib.util.find_spec(__name__).origin).parent
    static_folder = html_report_root / "_static"
    report_folder = report_folder / "_static"

    shutil.copytree(static_folder, report_folder, dirs_exist_ok=True)
