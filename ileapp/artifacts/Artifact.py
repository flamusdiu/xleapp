import os
import traceback
from abc import ABC, abstractmethod
from time import process_time

from html_report.web_icons import Icon
from helpers.ilapfuncs import is_platform_windows
from html_report.artifact_report import ArtifactHtmlReport


class AbstractArtifact(ABC):
    """Abstract class for creating Artifacts
    """

    _core_artifact = False
    _long_running_process = False
    _web_icon = Icon.ALERT_TRIANGLE

    def __init__(self, name):
        self._name = name
        self._category = 'None'
        self._artifact_report = ArtifactHtmlReport()

    @abstractmethod
    def get(files_found, seeker):
        """Gets artifacts located in `files_found` params by the
        `seeker`. It saves should save the report in `report_folder`.

        Args:
            files_found (tuple): list of files found
                by `seeker`
            report_folder (str): location of the `report_folder` to save
                report of artifact
            seeker (FileSeekerBase): object to search for files
        """
        print("Needs to implement AbastractArtifact's get() method!")

    @property
    def long_running_process(self):
        """True if this artifact takes an extremely long time to run.

            Set to true to mark this artifact has having an extremely
            long run time during processing of the artifact. Artifacts
            whose run time is greater then 2 mins probably need to
            have this value set.

            This will cause the artifact not to be select by default
            when using the GUI;

            Returns:
                bool: True/False if long running process
        """
        return self._long_running_process

    @property
    def web_icon(self):
        """
        str: Returns Bootstrap web icon class for this artifact
        """
        return self._web_icon

    @property
    def name(self):
        """
        str: Long name of the Artifact
        """
        return self._name

    @property
    def search_dirs(self):
        """
        tuple: Tuple containing search regex for
        location of files containing the Artifact.
        """
        return self._search_dirs

    @property
    def category(self):
        """
        str: Section of the report the artifacts shows under.
        """
        return self._category

    @property
    def core_artifact(self):
        """bool: Sets if this is a core artifact
        """
        return self._core_artifact

    @property
    def artifact_report(self):
        """Returns object for the artifact html report

        Call `self.artifact_report.init()` and pass in report name
        to set it.

        Returns:
            ArtifactHtmlReport: artifact html report object
        """
        return self._artifact_report

    @artifact_report.setter
    def artifact_report(self, artifact_report):
        self.artifact_report = artifact_report

    @property
    def report_folder(self):
        """Wrapper for the report folder object
        """
        return self._props.run_time_info['report_folder']

    @property
    def file_found(self):
        """list: files or folders found for an artifact
        """
        self._files_found

    @file_found.setter
    def file_found(self, files):
        self._files_found = files

    @property
    def data(self):
        """list: data found per artifact
        """
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def process(self, files_found, seeker, report_folder_base):
        """Processes artifact

           1. Create the report folder for it
           2. Fetch the method (function) and call it
           3. Wrap processing function in a try..except block

        Args:
            files_found (tuple): list of files found by
                seeker
            report_folder (str): location of the :obj:`report_folder`
                to save report of artifact
            seeker (FileSeekerBase): object to search for files
        """
        start_time = process_time()
        slash = '\\' if is_platform_windows() else '/'
        artifact_short_name = type(self).__name__
        logfunc(f'{self.report_section} [{artifact_short_name}] artifact'
                f'executing')
        report_folder = os.path.join(report_folder_base, self.name) + slash
        try:
            if os.path.isdir(report_folder):
                pass
            else:
                os.makedirs(report_folder)
        except Exception as ex:
            logfunc(f'Error creating {self.name} report '
                    f'directory at path {report_folder}')
            logfunc(f'Reading {self.name} artifact failed!')
            logfunc(f'Error was {ex}')
            return
        try:
            self.get(files_found, report_folder, seeker)
        except Exception as ex:
            logfunc(f'Reading {self.name} artifact had errors!')
            logfunc(f'Error was {ex}')
            logfunc(f'Exception Traceback: {traceback.format_exc()}')
            return

        end_time = process_time()
        run_time_secs = end_time - start_time
        # run_time_HMS = strftime('%H:%M:%S', gmtime(run_time_secs))
        logfunc(f'{self.report_section} [{artifact_short_name}] artifact '
                f'completed in time {run_time_secs} seconds')
