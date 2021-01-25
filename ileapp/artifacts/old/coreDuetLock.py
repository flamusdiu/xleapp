from html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport
from helpers.ilapfuncs import timeline, tsv
from helpers.db import open_sqlite_db_readonly

from artifacts.Artifact import AbstractArtifact


class CoreDuetLock(AbstractArtifact):

    _name = 'CoreDuet Lock State'
    _search_dirs = ('**/coreduetd.db')
    _category = 'CoreDuet'
    _web_icon = Icon.LOCK

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
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
