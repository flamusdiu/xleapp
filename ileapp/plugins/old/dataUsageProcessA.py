from helpers.db import open_sqlite_db_readonly
from helpers import timeline, tsv
from ileapp.html_report import Icon

from artifacts.Artifact import AbstractArtifact


class DataUsageProcessA(ab.AbstractArtifact):

    _name = 'Data Usage Process'
    _search_dirs = ('**/DataUsage-watch.sqlite')
    _category = 'Data Usage'
    _web_icon = Icon.WIFI

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute("""
        select
        datetime(zprocess.ztimestamp+ 978307200, 'unixepoch'),
        datetime(zprocess.zfirsttimestamp + 978307200, 'unixepoch'),
        zprocess.zprocname,
        zprocess.zbundlename
        from zprocess
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3]))

            report = ArtifactHtmlReport('Data Usage')
            report.start_artifact_report(report_folder, 'Data Usage Process')
            report.add_script()
            data_headers = ('Timestamp','Process First Timestamp','Process Name','Bundle ID')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Data Usage Process'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Data Usage Process'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Data Usage available')

        db.close()
