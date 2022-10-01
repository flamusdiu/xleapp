"""
xLEAPP
"""
from ._authors import __authors__, __contributors__
from ._version import __project__, __version__
from .artifact import Artifact as Artifact
from .artifact import ArtifactError as ArtifactError
from .artifact import Search as Search
from .artifact import core_artifact as core_artifact
from .artifact import long_running_process as long_running_process
from .helpers.db import open_sqlite_db_readonly as open_sqlite_db_readonly
from .helpers.decorators import timed as timed
from .report import WebIcon as WebIcon
from .templating import ArtifactHtmlReport as ArtifactHtmlReport
from .templating import Template as Template


VERSION = f"{__project__} {__version__}"
