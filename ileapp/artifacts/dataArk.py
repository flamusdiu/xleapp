import os
import plistlib
import sqlite3

from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import is_platform_windows, logdevinfo, logfunc, tsv

from artifacts.Artifact import AbstractArtifact


class DataArk(AbstractArtifact):

    _name = 'Data Ark'
    _search_dirs = ('**/Library/Lockdown/data_ark.plist')
    _report_section = 'IOS Build'

    @staticmethod
    def get(files_found, report_folder, seeker):
        data_list = []
        file_found = str(files_found[0])
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                data_list.append((key, val))
                
                if key == "-DeviceName":
                    logdevinfo(f"Device name: {val}")
                if key == "-TimeZone":
                    logdevinfo(f"Timezone per Data Ark: {val}")
                if key == "com.apple.iTunes.backup-LastBackupComputerName":
                    logdevinfo(f"Last backup computer name: {val}")
                if key == ("com.apple.iTunes.backup-LastBackupComputerType"):
                    logdevinfo(f"Last backup computer type: {val}")
    
        report = ArtifactHtmlReport('Data Ark')
        report.start_artifact_report(report_folder, 'Data Ark')
        report.add_script()
        data_headers = ('Key','Values' )     
        report.write_artifact_data_table(data_headers, data_list, file_found)
        report.end_artifact_report()
        
        tsvname = 'Data Ark'
        tsv(report_folder, data_headers, data_list, tsvname)
                