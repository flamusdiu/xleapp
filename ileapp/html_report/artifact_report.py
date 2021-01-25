import html
import os
import jinja2
from helpers import is_platform_windows
from helpers.version_info import aleapp_version


class ArtifactHtmlReport:

    def __init__(self):
        self.artifact_name = 'Artifact'
        self.report_file = None
        self.report_file_path = ''
