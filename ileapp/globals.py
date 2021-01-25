import datetime
import os
from collections import ChainMap, defaultdict
from pathlib import Path

import artifacts

THUMBNAIL_ROOT = '**/Media/PhotoData/Thumbnails/**'
MEDIA_ROOT = '**/Media'
THUMB_SIZE = 256, 256


class Props(object):
    """Global Properties class.
    """
    _core_artifacts = {}
    _artifact_list = {}
    _selected_artifacts = {}
    _run_time_info = defaultdict(lambda: None)

    def init(self):
        self._artifact_list = artifacts.get_list_of_artifacts(ordered=False)

        self._core_artifacts = {
            [(name, artifact) for name, artifact in self._artifact_list.items()
             if artifact.cls.core_artifact is True]
        }

        # Deletes core artifacts from main list
        for name, artifact in self._core_artifacts:
            self._artifact_list.pop(name)

        self.run_time_info['progress_bar_total'] = (
            len(self.installed_artifacts))

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
        artifact_list = ChainMap(self.core_artifacts,
                                 self.artifact_list,
                                 self.selected_artifacts)
        return sorted(list(artifact_list))

    @property
    def selected_artifacts(self):
        """dict: Selected artifacts to run
        """
        return self._selected_artifacts

    def select_artifact(self, name):
        """Adds an artifacts to be selected and run.
        """
        artifact = self._artifact_list.pop(name)
        self._selected_artifacts.update(artifact)

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
        return self.run_time_info

    def set_output_folder(self, output_folder):
        """Sets and creates output folders for the reports

        Args:
            output_folder (str or Path): output folder for reports
        """
        now = datetime.datetime.now()
        current_time = now.strftime('%Y-%m-%d_%A_%H%M%S')

        report_folder_base = (Path(output_folder) /
                              f'iLEAPP_Reports_{current_time}')

        self.run_time_info['report_folder_base'] = report_folder_base

        temp_folder = report_folder_base / 'temp'

        self.run_time_info['temp_folder'] = temp_folder

        self.run_time_info['log_folder'] = report_folder_base / 'Script Logs'

        os.makedirs(os.path.join(report_folder_base, 'Script Logs'))
        os.makedirs(temp_folder)


# Global Class
props = Props()
