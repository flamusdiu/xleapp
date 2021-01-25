from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import open_sqlite_db_readonly, timeline, tsv

from artifacts.Artifact import AbstractArtifact


class QueryPredictions(AbstractArtifact):
    _name = 'Query Predictions'
    _search_dirs = ('**/query_predictions.db')
    _category = 'SMS & iMessage'

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        select
        datetime(creationTimestamp, "UNIXEPOCH") as START,
        content,
        isSent,
        conversationId,
        id,
        uuid
        from messages
        ''')
        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5]))

            report = ArtifactHtmlReport('Query Predictions')
            report.start_artifact_report(report_folder, 'Query Predictions')
            report.add_script()
            data_headers = ('Timestamp', 'Content', 'Is Sent?', 'Conversation ID', 'ID', 'UUID')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Query Predictions'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Query Predictions'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No data available in table')

        db.close()
