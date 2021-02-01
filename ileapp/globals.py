import datetime
import logging
from collections import ChainMap, defaultdict
from pathlib import Path
from ileapp import VERSION

import jinja2

THUMBNAIL_ROOT = '**/Media/PhotoData/Thumbnails/**'
MEDIA_ROOT = '**/Media'
THUMB_SIZE = 256, 256


class Device:
    """Class to hold device information
    """
    def __init__(self, **kwargs):
        for it in kwargs:
            self.__dict__[it] = kwargs[it]


class Props:
    """Global Properties class.
    """
    _core_artifacts = {}
    _artifact_list = {}
    _selected_artifacts = []
    _run_time_info = defaultdict(lambda: None)
    _logger = logging
    _device_info = Device

    def init(self, artifacts):
        """Initializes the global properties object

            Run `props.init()` to initialize the artifacts
            before attempting to use the artifact object.
        """
        self._artifact_list = (
            artifacts.get_list_of_artifacts(self, ordered=False)
        )

        for name, artifact in self._artifact_list.items():
            if artifact.cls.core_artifact is True:
                self._core_artifacts.update({name: artifact})

        for name, artifact in self._core_artifacts.items():
            self._artifact_list.pop(name)

        self.run_time_info['progress_bar_total'] = (
            len(self.installed_artifacts))

    @property
    def version(self):
        return VERSION

    @property
    def core_artifacts(self):
        """Returns all mandatory artifacts

        This artifacts ALWAYS run. No matter
        which artifacts are selected.

        Returns:
            dict: list of artifacts
        """
        return self._core_artifacts

    @property
    def installed_artifacts(self):
        """List: list of strings of installed artifacts
        """
        return ChainMap(self.core_artifacts, self.artifact_list)

    @property
    def selected_artifacts(self):
        """dict: Selected artifacts to run
        """
        return self._selected_artifacts

    def select_artifact(self, name):
        """Adds an artifacts to be selected and run.
        """
        if name in list(self.artifact_list):
            self._selected_artifacts.append(name)

    def deselect_artifact(self, name):
        """Adds an artifacts to be selected and run.
        """
        if (name in list(self.selected_artifacts)
                and name not in list(self.core_artifacts)):
            self._selected_artifacts.remove(name)

    def set_progress_bar(self, val):
        """Sets the progress bar for the GUI

        Args:
            val (int): how much progress is on the bar
        """
        window = self.run_time_info['window_handle']
        window['-PROGRESSBAR-'].update_bar(val)

    @property
    def run_time_info(self):
        """defaultdict: returns program run state information
        """
        return self._run_time_info

    @property
    def artifact_list(self):
        return self._artifact_list

    @property
    def device_info(self):
        return self._device_info

    @device_info.setter
    def device_info(self, **kwargs):
        self._device_info = Device(**kwargs)

    def set_output_folder(self, output_folder):
        """Sets and creates output folders for the reports

        Args:
            output_folder (str or Path): output folder for reports
        """
        now = datetime.datetime.now()
        current_time = now.strftime('%Y-%m-%d_%A_%H%M%S')

        report_folder_base = (
            Path(output_folder) / f'iLEAPP_Reports_{current_time}'
        )

        self.run_time_info['report_folder_base'] = report_folder_base

        temp_folder = report_folder_base / 'temp'

        self.run_time_info['temp_folder'] = temp_folder

        self.run_time_info['log_folder'] = report_folder_base / 'Script Logs'

        self.run_time_info['log_folder'].mkdir(parents=True, exist_ok=True)
        self.run_time_info['temp_folder'].mkdir(parents=True, exist_ok=True)


# Global Class
props = Props()
jinja = jinja2.Environment
