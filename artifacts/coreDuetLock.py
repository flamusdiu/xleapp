import glob
import json
import os
import pathlib
import plistlib
import sqlite3

from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import (is_platform_windows, logfunc,
                             open_sqlite_db_readonly, timeline, tsv)

from .Artifact import AbstractArtifact


class CoreDuetLock(AbstractArtifact):
        
    _name = 'CoreDuet Lock State'
    _search_dirs = ('**/coreduetd.db')
    _report_section = 'CoreDuet'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute(
        """
        select 
        datetime(zcreationdate+978307200,'unixepoch'),
        time(zlocaltime,'unixepoch'),
        time(zcreationdate-zlocaltime,'unixepoch'),
        case zlockstate
        when '0' then 'unlocked'
        when '1' then 'locked'
        end
        from zcddmscreenlockeven	
        """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []    
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3] ))

            description = ''
            report = ArtifactHtmlReport('CoreDuet Lock State')
            report.start_artifact_report(report_folder, 'Lock State', description)
            report.add_script()
            data_headers = ('Create Time','Local Device Time','Time Zone','Lock State' )     
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()
            
            tsvname = 'CoreDuet Lock State'
            tsv(report_folder, data_headers, data_list, tsvname)
            
            tlactivity = 'CoreDuet Lock State'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No data available in table')
        