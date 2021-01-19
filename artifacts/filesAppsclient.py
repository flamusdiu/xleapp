import datetime
import glob
import os
import sqlite3

import nska_deserialize as nd
from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import (is_platform_windows, logfunc,
                             open_sqlite_db_readonly, timeline, tsv)

from .Artifact import AbstractArtifact


class FilesAppsClient(AbstractArtifact):

    _name = 'Files App - iCloud Client Items'
    _search_dirs = ('*private/var/mobile/Library/Application Support/CloudDocs/session/db/client.db*')
    _report_section = 'Files App'

    @staticmethod
    def get(files_found, report_folder, seeker):
        for file_found in files_found:
            file_found = str(file_found)
            
            if file_found.endswith('client.db'):
                break
                
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        item_birthtime,
        item_filename,
        version_mtime
        FROM
        client_items
        ''')
        
        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:
            for row in all_rows:
                birthtime = datetime.datetime.fromtimestamp(row[0])
                versionmtime = datetime.datetime.fromtimestamp(row[2])
                data_list.append((birthtime, row[1], versionmtime))
                
            description = '	Items stored in iCloud Drive with metadata about files. '
            report = ArtifactHtmlReport('Files App - iCloud Client Items')
            report.start_artifact_report(report_folder, 'Files App - iCloud Client Items', description)
            report.add_script()
            data_headers = ('Birthtime', 'Filename', 'Version Modified Time' )     
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()
            
            tsvname = 'Files App - iCloud Client Items'
            tsv(report_folder, data_headers, data_list, tsvname)
        
            tlactivity = 'Files App - iCloud Client Items'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Files App - iCloud Client Items data available')
        
