from html_report.artifact_report import ArtifactHtmlReport
from packaging import version  # use to search per version number
from tools.ilapfuncs import logfunc, open_sqlite_db_readonly

import artifacts.artGlobals  # use to get iOS version -> iOSversion = artifacts.artGlobals.versionf

from .Artifact import AbstractArtifact


class TCC (AbstractArtifact):

    _name = 'TCC - Permissions'
    _search_dirs = ('*TCC.db*')
    _report_section = 'App Permissions'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)

        iOSversion = artifacts.artGlobals.versionf
        if version.parse(iOSversion) >= version.parse("9"):
            cursor = db.cursor()
            cursor.execute('''
            select client,
            service,
            datetime(last_modified,'unixepoch')
            from access
            order by client
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2]))

            if usageentries > 0:
                report = ArtifactHtmlReport('TCC - Permissions')
                report.start_artifact_report(report_folder, 'TCC - Permissions')
                report.add_script()
                data_headers = ('Bundle ID','Permissions', 'Last Modified Timestamp')
                report.write_artifact_data_table(data_headers, data_list, file_found, html_escape=False)
                report.end_artifact_report()

                '''
                tsvname = 'InteractionC Contacts'
                tsv(report_folder, data_headers, data_list, tsvname)

                tlactivity = 'InteractonC Contacts'
                timeline(report_folder, tlactivity, data_list, data_headers)
                '''
            else:
                logfunc('No data available in TCC database.')

            db.close()
