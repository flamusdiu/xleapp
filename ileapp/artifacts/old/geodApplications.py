import base64
import json
import os
import sqlite3

from html_report.artifact_report import ArtifactHtmlReport
from packaging import version
from helpers import(is_platform_windows,
                             open_sqlite_db_readonly, timeline, tsv)

import artifacts.artGlobals

from artifacts.Artifact import AbstractArtifact


class GeodApplication(ab.AbstractArtifact):

    _name = 'GeoD Application'
    _search_dirs = '**/AP.db'
    _category = 'Applications'

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute(
        """
        SELECT count_type, app_id, createtime
        FROM mkcount
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[2], row[0], row[1] ))
                description = ''
            report = ArtifactHtmlReport('Geolocation')
            report.start_artifact_report(report_folder, 'Applications', description)
            report.add_script()
            data_headers = ("Creation Time", "Count ID", "Application")
            report.write_artifact_data_table(data_headers, data_list, file_found, html_escape = False)
            report.end_artifact_report()

            tsvname = 'Geolocation Applications'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Geolocation Applications'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for Geolocation Applications')

        db.close()
