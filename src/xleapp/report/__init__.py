# -*- coding: utf-8 -*-
"""
Reports Module
"""

import importlib.util
import shutil
import typing as t

from pathlib import Path

from .webicons import WebIcon as WebIcon


def copy_static_files(report_folder: Path) -> None:
    """Copies static files to report folder.

    Returns:
        None
    """
    mod = importlib.util.find_spec(__name__)
    if mod and mod.origin:
        html_report_root = Path(mod.origin).parent
        static_folder = html_report_root / "_static"
        report_folder = report_folder / "_static"

        shutil.copytree(static_folder, report_folder, dirs_exist_ok=True)
