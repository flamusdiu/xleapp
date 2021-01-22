import os
import traceback
from abc import ABC, abstractmethod
from time import process_time

from gui.modules.web_icons import Icon
from tools.ilapfuncs import is_platform_windows, logfunc


class AbstractArtifact(ABC):
    """Abstract class for creating Artifacts
    """

    _name = 'AbstractArtifact'
    _search_dirs = ()
    _report_section = ''
    _web_icon = Icon.ALERT_TRIANGLE
    _long_running_process = False
    _core_artifact = False

    @staticmethod
    @abstractmethod
    def get(files_found, report_folder, seeker):
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
    def report_section(self):
        """
        str: Section of the report the artifacts shows under.
        """
        return self._report_section

    @property
    def core_artifact(self):
        """bool: Sets if this is a core artifact
        """
        return self._core_artifact

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
