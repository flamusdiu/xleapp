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

class AggDict(AbstractArtifact):
        
    _name = 'Aggregate Dictionary'
    _search_dirs = ('*/AggregateDictionary/ADDataStore.sqlitedb')
    _report_section = 'Aggregate Dictionary'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        select
        date(distributionkeys.dayssince1970*86400, 'unixepoch'),
        distributionkeys.key,
        distributionvalues.value,
        distributionvalues.secondsindayoffset,
        distributionvalues.distributionid
        from
        distributionkeys, distributionvalues 
        where distributionkeys.rowid = distributionvalues.distributionid
        """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:    
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4] ))

            description = ''
            report = ArtifactHtmlReport('Aggregate Dictionary Distributed Keys')
            report.start_artifact_report(report_folder, 'Distributed Keys', description)
            report.add_script()
            data_headers = ('Day','Key','Value','Seconds in Day Offset','Distribution Values Table ID' )     
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()
            
            tsvname = 'Agg Dict Dist Keys'
            tsv(report_folder, data_headers, data_list, tsvname)
            
            tlactivity = 'Aggregate Dictionary Distributed Keys'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc("No Aggregate Dictionary Distributed Keys Data available")
        
        