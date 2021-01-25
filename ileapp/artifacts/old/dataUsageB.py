from html_report.artifact_report import ArtifactHtmlReport
from helpers.ilapfuncs import timeline, tsv
from helpers.db import open_sqlite_db_readonly
from html_report import Icon
from artifacts.Artifact import AbstractArtifact


class DataUsageB(AbstractArtifact):

    _name = 'Data Usage'
    _search_dirs = ('**/DataUsage-watch.sqlite')
    _category = 'Data Usage'
    _web_icon = Icon.WIFI

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        select
        datetime(zprocess.ztimestamp + 978307200, 'unixepoch'),
        datetime(zprocess.zfirsttimestamp + 978307200, 'unixepoch'),
        datetime(zliveusage.ztimestamp + 978307200, 'unixepoch'),
        zbundlename,
        zprocname,
        zwifiin,
        zwifiout,
        zwwanin,
        zwwanout
        from zliveusage, zprocess
        where zprocess.z_pk = zliveusage.zhasprocess
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]))

            report = ArtifactHtmlReport('Data Usage')
            report.start_artifact_report(report_folder, 'Data Usage')
            report.add_script()
            data_headers = ('Process Timestamp', 'Process First Timestamp', 'Live Usage Timestamp', 'Bundle ID', 'Process Name', 'WIFI In', 'WIFI Out', 'WWAN IN', 'WWAN Out')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Data Usage'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Data Usage'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Data Usage available')

        db.close()
