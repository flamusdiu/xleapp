import os
import traceback
from abc import ABC, abstractmethod
from time import process_time

from tools.ilapfuncs import logfunc, is_platform_windows


class AbstractArtifact(ABC):

    _name = 'AbstractArtifact'
    _search_dirs = ()
    _report_section = ''

    @staticmethod
    @abstractmethod
    def get(files_found, report_folder, seeker):
        print("Needs to implement AbastractArtifact's get() method!")

    @property
    def name(self):
        return self._name

    @property
    def search_dirs(self):
        return self._search_dirs

    @property
    def report_section(self):
        return self._report_section

    def process(self, files_found, seeker, report_folder_base):
        ''' Perform the common setup for each artifact, ie, 
            1. Create the report folder for it
            2. Fetch the method (function) and call it
            3. Wrap processing function in a try..except block

            Args:
                files_found: list of files that matched regex

                artifact_func: method to call

                artifact_name: Pretty name of artifact

                seeker: FileSeeker object to pass to method
        '''
        start_time = process_time()
        slash = '\\' if is_platform_windows() else '/'
        artifact_short_name = type(self).__name__
        logfunc(f'{self.report_section} [{artifact_short_name}] artifact executing')
        report_folder = os.path.join(report_folder_base, self.name) + slash
        try:
            if os.path.isdir(report_folder):
                pass
            else:
                os.makedirs(report_folder)
        except Exception as ex:
            logfunc(f'Error creating {self.name} report directory at path {report_folder}')
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
        logfunc(f'{self.report_section} [{artifact_short_name}] artifact completed in time {run_time_secs} seconds')
