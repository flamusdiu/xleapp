import datetime

from helpers.db import open_sqlite_db_readonly
from helpers import timeline, tsv
from ileapp.html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport

from artifacts.Artifact import AbstractArtifact


class FilesAppsClient(AbstractArtifact):

    _name = 'Files App - iCloud Client Items'
    _search_dirs = ('*private/var/mobile/Library/Application Support/CloudDocs/session/db/client.db*')
    _category = 'Files App'
    _web_icon = Icon.FILES_TEXT

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
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

