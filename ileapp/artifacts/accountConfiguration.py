import plistlib

from gui.modules.web_icons import Icon
from html_report.artifact_report import ArtifactHtmlReport
from helpers import tsv

from artifacts.Artifact import AbstractArtifact


class AccountConfiguration(AbstractArtifact):

    _name = 'Account Configuration'
    _search_dirs = ('**/com.apple.accounts.exists.plist')
    _report_section = 'Accounts'
    _web_icon = Icon.USER


    @staticmethod
    def get(files_found, report_folder, seeker):
        data_list = []
        file_found = str(files_found[0])
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                data_list.append((key, val))

        report = ArtifactHtmlReport('Account Configuration')
        report.start_artifact_report(report_folder, 'Account Configuration')
        report.add_script()
        data_headers = ('Key', 'Values')
        report.write_artifact_data_table(data_headers, data_list, file_found)
        report.end_artifact_report()

        tsvname = 'Account Configuration'
        tsv(report_folder, data_headers, data_list, tsvname)
