from html_report.artifact_report import ArtifactHtmlReport
from packaging import version  # use to search per version number
from tools.ilapfuncs import(kmlgen,
                             open_sqlite_db_readonly, timeline, tsv)

import artifacts.artGlobals  # use to get iOS version -> iOSversion = artifacts.artGlobals.versionf

from artifacts.Artifact import AbstractArtifact


class RoutineDVehicleLocation(AbstractArtifact):

    _name = 'RoutineD Vehicle Location'
    _search_dirs = ('**/Local.sqlite')
    _category = 'Locations'

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)

        iOSversion = artifacts.artGlobals.versionf
        if version.parse(iOSversion) >= version.parse("12"):
            cursor = db.cursor()
            cursor.execute('''
            select
            datetime(zrtvehicleeventmo.zdate + 978307200, 'unixepoch'),
            datetime(zrtvehicleeventmo.zlocdate + 978307200, 'unixepoch'),
            zvehicleidentifier,
            zlocuncertainty,
            zidentifier,
            zlocationquality,
            zusersetlocation,
            zusuallocation,
            znotes,
            zphotodata,
            zloclatitude,
            zloclongitude
            from
            zrtvehicleeventmo
            ''')
        else:
            cursor = db.cursor()
            cursor.execute('''
            select
            datetime(zrtvehicleeventmo.zdate + 978307200, 'unixepoch'),
            datetime(zrtvehicleeventmo.zlocdate + 978307200, 'unixepoch'),
            zvehicleidentifier,
            zlocuncertainty,
            zidentifier,
            zlocationquality,
            zusersetlocation,
            zusuallocation,
            znotes,
            zgeomapitem,
            zphotodata,
            zloclatitude,
            zloclongitude
            from
            zrtvehicleeventmo
                ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []

            if version.parse(iOSversion) >= version.parse("12"):

                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]))

                report = ArtifactHtmlReport('RoutineD Vehicle Location')
                report.start_artifact_report(report_folder, 'Vehicle Location')
                report.add_script()
                data_headers = ('Timestamp','Location Date','Vehicle Identifier', 'Location Identifier', 'Identifier','Location Quality','User Set Location','Usual Location','Notes','Photo Data','Latitude','Longitude')
                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = 'RoutineD Vehicle Location'
                tsv(report_folder, data_headers, data_list, tsvname)

                tlactivity = 'RoutineD Vehicle Location'
                timeline(report_folder, tlactivity, data_list, data_headers)

                kmlactivity = 'RoutineD Vehicle Location'
                kmlgen(report_folder, kmlactivity, data_list, data_headers)
            else:
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]))

                report = ArtifactHtmlReport('RoutineD Vehicle Location')
                report.start_artifact_report(report_folder, 'Vehicle Location')
                report.add_script()
                data_headers = ('Timestamp', 'Location Date', 'Vehicle Identifier', 'Location Identifier', 'Identifier', 'Location Quality', 'User Set Location', 'Usual Location', 'Notes', 'Geo Map Item', 'Photo Data', 'Latitude', 'Longitude')
                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = 'RoutineD Vehicle Location'
                tsv(report_folder, data_headers, data_list, tsvname)

                tlactivity = 'RoutineD Vehicle Location'
                timeline(report_folder, tlactivity, data_list, data_headers)

                kmlactivity = 'RoutineD Vehicle Location'
                kmlgen(report_folder, kmlactivity, data_list, data_headers)
        else:
            logfunc('No data available in RoutineD Vehicle Location')

        db.close()
