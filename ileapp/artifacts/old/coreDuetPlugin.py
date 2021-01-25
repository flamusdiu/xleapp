from html_report.artifact_report import ArtifactHtmlReport
from helpers.ilapfuncs import timeline, tsv
from helpers.db import open_sqlite_db_readonly
from html_report import Icon
from artifacts.Artifact import AbstractArtifact


class CoreDuetPlugin(AbstractArtifact):

    _name = 'CoreDuet Plugged In'
    _search_dirs = ('**/coreduetd.db')
    _category = 'CoreDuet'
    _web_icon = Icon.BATTERY_CHARGING

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
            time(zcreationdate-zlocaltime,'unixepoch'),
            case zcablestate
            when '0' then 'unplugged'
            when '1' then 'plugged in'
            end
            from zcddmpluginevent
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
            report = ArtifactHtmlReport('CoreDuet Plugged In')
            report.start_artifact_report(report_folder, 'Plugged In', description)
            report.add_script()
            data_headers = ('Timestamp', 'Time Zone', 'Cable State')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'CoreDuet Plugged In'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Coreduet Plugged In'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No data available in table')
