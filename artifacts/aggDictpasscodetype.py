
from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import open_sqlite_db_readonly, tsv

from artifacts.Artifact import AbstractArtifact


class AggDictPasscodeType(AbstractArtifact):

    _name = 'Aggregate Dictionary Passcode Type'
    _search_dirs = ('*/AggregateDictionary/ADDataStore.sqlitedb')
    _report_section = 'Aggregate Dictionary'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        select
        date(dayssince1970*86400, 'unixepoch'),
        key,
        case
        when value=-1 then '6-digit'
        when value=0 then 'no passcode'
        when value=1 then '4-digit'
        when value=2 then 'custom alphanumeric'
        when value=3 then 'custom numeric'
        else "n/a"
        end "value"
        from
        scalars
        where key like 'com.apple.passcode.passcodetype%'
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)

        if usageentries > 0:
            data_list = []    
            for row in all_rows:
                data_list.append((row[0], row[1], row[2]))

            description = ''
            report = ArtifactHtmlReport('Aggregate Dictionary Passcode Type')
            report.start_artifact_report(report_folder, 'Passcode Type',
                                         description)
            report.add_script()
            data_headers = ('Day', 'Key', 'Value')
            report.write_artifact_data_table(data_headers, data_list,
                                             file_found)
            report.end_artifact_report()

            tsvname = 'Agg Dict Dictionary Passcode Type'
            tsv(report_folder, data_headers, data_list, tsvname)
