import json
import os

from helpers.ilapfuncs import tsv
from html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport

from artifacts.Artifact import AbstractArtifact


class DiscordManifest(AbstractArtifact):

    _name = 'Discord Manifest'
    _search_dirs = ('*/private/var/mobile/Containers/Data/Application/*/Documents/RCTAsyncLocalStorage_V1/manifest.json')
    _category = 'Discord'
    _web_icon = Icon.FILE_TEXT

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        data_list = []
        for file_found in files_found:
            file_found = str(file_found)

            if os.path.isfile(file_found):
                with open(file_found) as f_in:
                    for jsondata in f_in:
                        jsonfinal = json.loads(jsondata)

            for key, value in jsonfinal.items():
                data_list.append((key, value))

        if len(data_list) > 0:
            report = ArtifactHtmlReport('Discord Manifest')
            report.start_artifact_report(report_folder, 'Discord Manifest')
            report.add_script()
            data_headers = ('Key', 'Value')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Discord Manifest'
            tsv(report_folder, data_headers, data_list, tsvname)
