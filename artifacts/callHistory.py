from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import (is_platform_windows, logfunc,
                             open_sqlite_db_readonly, timeline, tsv)

from artifacts.Artifact import AbstractArtifact


class CallHistory(AbstractArtifact):

    _name = 'Call Logs'
    _search_dirs = ('**/CallHistory.storedata')
    _report_section = 'Call Logs'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT 
        Z_PK as "CALL ID",
        ZADDRESS AS "ADDRESS", 
        ZANSWERED AS "WAS ANSWERED", 
        ZCALLTYPE AS "CALL TYPE", 
        ZORIGINATED AS "ORIGINATED", 
        ZDURATION AS "DURATION (IN SECONDS)",
        ZISO_COUNTRY_CODE as "ISO COUNTY CODE",
        ZLOCATION AS "LOCATION", 
        ZSERVICE_PROVIDER AS "SERVICE PROVIDER",
        DATETIME(ZDATE+978307200,'UNIXEPOCH') AS "TIMESTAMP"
        FROM ZCALLRECORD  
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                an = str(row[1])
                an = an.replace("b'", "")
                an = an.replace("'", "")
                data_list.append((row[9], row[0], an, row[2], row[3], row[4], row[5], row[6], row[7], row[8]))

            report = ArtifactHtmlReport('Call Logs')
            report.start_artifact_report(report_folder, 'Call Logs')
            report.add_script()
            data_headers = ('Timestamp', 'Call ID', 'Address', 'Was Answered', 'Call Type', 'Originated', 'Duration in Secs', 'ISO County Code', 'Location', 'Service Provider')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()
            
            tsvname = 'Call Logs'
            tsv(report_folder, data_headers, data_list, tsvname)
            
            tlactivity = 'Call Logs'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Call Logs data available')

        db.close()
