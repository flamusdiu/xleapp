# -*- coding: utf-8 -*-
"""
xLEAPP
"""

from ._authors import __authors__, __contributors__
from ._version import __project__, __version__
from .artifacts import Artifact, Search, core_artifact, long_running_process
from .helpers.db import open_sqlite_db_readonly
from .helpers.decorators import timed
from .report import WebIcon
from .templating import ArtifactHtmlReport, Template


VERSION = f"{__project__} v{__version__}"
