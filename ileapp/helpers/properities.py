import datetime
import os
from collections import ChainMap

from artifacts import get_list_of_artifacts

THUMBNAIL_ROOT = '**/Media/PhotoData/Thumbnails/**'
MEDIA_ROOT = '**/Media'
THUMB_SIZE = 256, 256


class Props(object):
    """Global Properties class.
    """
    _core_artifacts = {}
    _artifact_list = {}
    _selected_artifacts = {}
    _run_time_information = {
        'ios_version': '0',
        'window_handle': object(),
        'progress_bar_total': 0
    }

    def __init__(self):
        self._artifact_list = get_list_of_artifacts(ordered=False)

        self._core_artifacts = {
            [(name, artifact) for name, artifact in self._artifact_list.items()
             if artifact.cls.core_artifact is True]
        }

        # Deletes core artifacts from main list
        [self._artifact_list.pop(name)
         for name, artifact in self._core_artifacts]

         self.run_time_information['progress_bar_total'] = len(self.installed_artifacts)

    @property
    def run_time_information(self):
        return self.run_time_information

    @run_time_information.setter
    def run_time_information(self, key, val):
        self._run_time_information.update({key: val})

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
        artifact_list = ChainMap(self.core_artifacts,
                                 self.artifact_list,
                                 self.selected_artifacts)
        return sorted(list(artifact_list))

    @property
    def selected_artifacts(self):
        return self._selected_artifacts

    @property
    def output_parameters(self):
        return self._output_parameters or OutputParameters()

    @output_parameters.setter
    def output_parameters(self, output_path):
        self._output_parameters = OutputParameters(output_path)

    def select_artifact(self, name):
        artifact = self._artifact_list.pop(name)
        self._selected_artifacts.update(artifact)

    def set_progress_bar(self, val):
        window = self.run_time_information['window_handle']
        window['-PROGRESSBAR-'].update_bar(val)


class OutputParameters:
    '''Defines the parameters that are common for '''
    # static parameters
    nl = '\n'
    screen_output_file_path = ''

    def __init__(self, output_folder):
        now = datetime.datetime.now()
        currenttime = str(now.strftime('%Y-%m-%d_%A_%H%M%S'))
        self.report_folder_base = (
            os.path.join(output_folder, 'iLEAPP_Reports_' + currenttime))
        self.temp_folder = os.path.join(self.report_folder_base, 'temp')
        OutputParameters.screen_output_file_path = (
            os.path.join(self.report_folder_base,
                         'Script Logs', 'Screen Output.html'))
        OutputParameters.screen_output_file_path_devinfo = (
            os.path.join(self.report_folder_base,
                         'Script Logs', 'DeviceInfo.html'))

        os.makedirs(os.path.join(self.report_folder_base, 'Script Logs'))
        os.makedirs(self.temp_folder)


# Global Class
props = Props()
