import os
import plistlib

from html_report.artifact_report import ArtifactHtmlReport
from helpers import is_platform_windows,   tsv

from artifacts.Artifact import AbstractArtifact


class MobileBackup(ab.AbstractArtifact):
    _name = 'Mobile Backup'
    _search_dirs = ('*/Preferences/com.apple.MobileBackup.plist')
    _category = 'Mobile Backup'

    # Backup version of iOS, iOS version installed at the time of recovery,
    # recovery date, and whether the backup was restored from iCloud.
    def get(self, files_found, seeker):
        data_list = []
        file_found = str(files_found[0])

        with open(file_found, 'rb') as fp:
            pl = plistlib.load(fp)

            if 'BackupStateInfo' in pl.keys():
                for key, val in pl['BackupStateInfo'].items():
                    if key == 'isCloud':
                        data_list.append((key, val))
                    if key == 'date':
                        data_list.append((key, val))
            else:
                pass

            if 'RestoreInfo' in pl.keys():
                for key, val in pl['RestoreInfo'].items():
                    if key == 'BackupBuildVersion':
                        data_list.append((key, val))
                    if key == 'DeviceBuildVersion':
                        data_list.append((key, val))
                    if key == 'WasCloudRestore':
                        data_list.append((key, val))
                    if key == 'RestoreDate':
                        data_list.append((key, val))


        report = ArtifactHtmlReport('Mobile Backup')
        report.start_artifact_report(report_folder, 'Mobile Backup')
        report.add_script()
        data_headers = ('Key', 'Value')
        report.write_artifact_data_table(data_headers, data_list, file_found)
        report.end_artifact_report()

        tsvname = 'Mobile Backup'
        tsv(report_folder, data_headers, data_list, tsvname)
