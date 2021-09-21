import glob
import os
import pathlib
import sqlite3

from html_report.artifact_report import ArtifactHtmlReport
from helpers import(is_platform_windows, kmlgen,
                             open_sqlite_db_readonly, timeline, tsv)

from artifacts.Artifact import AbstractArtifact


class TileAppDB (ab.AbstractArtifact):
    _name = 'Tile App DB Info & Geolocation'
    _search_dirs = ('*private/var/mobile/Containers/Shared/AppGroup/*/com.thetileapp.tile-TileNetworkDB.sqlite*')
    _category = 'Locations'

    def get(self, files_found, seeker):
        for file_found in files_found:
            file_found = str(file_found)

            if file_found.endswith('tile-TileNetworkDB.sqlite'):
                break

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute("""
        SELECT
        datetime(ZTIMESTAMP,'unixepoch','31 years'),
        ZNAME,
        datetime(ZACTIVATION_TIMESTAMP,'unixepoch','31 years'),
        datetime(ZREGISTRATION_TIMESTAMP,'unixepoch','31 years'),
        ZALTITUDE,
        ZLATITUDE,
        ZLONGITUDE,
        ZID,
        ZNODE_TYPE,
        ZSTATUS,
        ZIS_LOST,
        datetime(ZLAST_LOST_TILE_COMMUNITY_CONNECTION,'unixepoch','31 years')
        FROM ZTILENTITY_NODE INNER JOIN ZTILENTITY_TILESTATE ON ZTILENTITY_NODE.ZTILE_STATE = ZTILENTITY_TILESTATE.Z_PK
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]))

                description = ''
                report = ArtifactHtmlReport('Tile App - Tile Information & Geolocation')
                report.start_artifact_report(report_folder, 'Tile App DB Info & Geolocation', description)
                report.add_script()
                data_headers = ('Timestamp','Tile Name','Activation Timestamp','Registration Timestamp','Altitude','Latitude','Longitude','Tile ID','Tile Type','Status','Is Lost?','Last Community Connection' )
                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = 'Tile App DB Info Geolocation'
                tsv(report_folder, data_headers, data_list, tsvname)

                tlactivity = 'Tile App DB Info Geolocation'
                timeline(report_folder, tlactivity, data_list, data_headers)

                kmlactivity = 'Tile App DB Info Geolocation'
                kmlgen(report_folder, kmlactivity, data_list, data_headers)
        else:
            logfunc('No Tile App DB data available')

        db.close()
