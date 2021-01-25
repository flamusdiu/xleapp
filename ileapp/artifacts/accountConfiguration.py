import plistlib

from html_report import Icon
from helpers import tsv

from artifacts import AbstractArtifact


class AccountConfiguration(AbstractArtifact):

    _name = 'Account Configuration'
    _search_dirs = ('**/com.apple.accounts.exists.plist')
    _category = 'Accounts'
    _web_icon = Icon.USER

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        data_list = []
        file_found = str(files_found[0])
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                data_list.append((key, val))

        self.data = data_list
        self.files_found = files_found

    def report(self):
        report_folder = self._props.run_time_info['report_folder_path']

        report = self.artifact_report
        report.start_artifact_report(report_folder, self.name)
        report.add_script()
        data_headers = ('Key', 'Values')
        report.write_artifact_data_table(data_headers, self.data,
                                         self.files_found)
        report.end_artifact_report()

        tsv(report_folder, data_headers, self.datat, self.name)
