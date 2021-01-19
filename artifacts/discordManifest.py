import json
import os
from pathlib import Path

from html_report.artifact_report import ArtifactHtmlReport
from packaging import version
from tools.ilapfuncs import (is_platform_windows, logdevinfo, logfunc,
                             timeline, tsv)

import artifacts.artGlobals

from .Artifact import AbstractArtifact


class DiscordManifest(AbstractArtifact):

    _name = 'Discord Manifest'
    _search_dirs = ('*/private/var/mobile/Containers/Data/Application/*/Documents/RCTAsyncLocalStorage_V1/manifest.json')
    _report_section = 'Discord'

    @staticmethod
    def get(files_found, report_folder, seeker):
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
            