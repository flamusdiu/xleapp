import datetime
import logging
from collections import ChainMap, defaultdict
from pathlib import Path
from ileapp import VERSION

import jinja2

THUMBNAIL_ROOT = '**/Media/PhotoData/Thumbnails/**'
MEDIA_ROOT = '**/Media'
THUMB_SIZE = 256, 256

VERSION = VERSION

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
