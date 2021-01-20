import datetime
import plistlib

from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import logfunc, open_sqlite_db_readonly, timeline, tsv

from artifacts.Artifact import AbstractArtifact


class BluetoothOther(AbstractArtifact):
    _name = 'Bluetooth Other'
    _search_dirs = ('**/com.apple.MobileBluetooth.ledevices.other.db')
    _report_section = 'Bluetooth'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT
        Name,
        Address,
        LastSeenTime,
        Uuid
        FROM
        OtherDevices
        order by Name desc
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []    
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[3]))

            description = ''
            report = ArtifactHtmlReport('Bluetooth Other LE')
            report.start_artifact_report(report_folder, 'Other LE', description)
            report.add_script()
            data_headers = ('Name','Address','UUID')     
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Bluetooth Other LE'
            tsv(report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No data available for Bluetooth Other')

        db.close()


class BluetoothPaired (AbstractArtifact):
    _name = 'Bluetooth Paired LE'
    _search_dirs = ('**/com.apple.MobileBluetooth.ledevices.paired.db')
    _report_section = 'Bluetooth'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = files_found[0]

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        select
        Uuid,
        Name,
        NameOrigin,
        Address,
        ResolvedAddress,
        LastSeenTime,
        LastConnectionTime
        from
        PairedDevices
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []    
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[6]))

            description = ''
            report = ArtifactHtmlReport('Bluetooth Paired LE')
            report.start_artifact_report(report_folder, 'Paired LE', description)
            report.add_script()
            data_headers = ('UUID','Name','Name Origin','Address','Resolved Address','Last Connection Time')     
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Bluetooth Paired LE'
            tsv(report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No data available for Bluetooth Paired LE')

        db.close()


class BluetoothPairedReg (AbstractArtifact):
    _name = 'Bluetooth Paired'
    _search_dirs = ('**/com.apple.MobileBluetooth.devices.plist')
    _report_section = 'Bluetooth'

    @staticmethod
    def get(files_found, report_folder, seeker):
        data_list = [] 
        file_found = str(files_found[0])
        with open(file_found, 'rb') as f:
            plist = plistlib.load(f)
            # print(plist)
        if len(plist) > 0:
            for x in plist.items():
                macaddress = x[0]
                # print(x[1])
                if 'LastSeenTime' in x[1]:
                    lastseen = x[1]['LastSeenTime']
                    lastseen = (datetime.datetime.fromtimestamp(int(lastseen)).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    lastseen = ''
                if 'UserNameKey' in x[1]:
                    usernkey = x[1]['UserNameKey']
                else:
                    usernkey = ''

                if 'Name' in x[1]:
                    nameu = x[1]['Name']
                else: 
                    nameu = ''
                if 'DeviceIdProduct' in x[1]:
                    deviceid = x[1]['DeviceIdProduct']
                else:
                    deviceid = ''
                if 'DefaultName' in x[1]:
                    defname = x[1]['DefaultName']
                else:
                    defname = ''

                data_list.append((lastseen, macaddress, usernkey, nameu, deviceid, defname))

            description = ''
            report = ArtifactHtmlReport('Bluetooth Paired')
            report.start_artifact_report(report_folder, 'Paired', description)
            report.add_script()
            data_headers = ('Last Seen Time','MAC Address','Name Key','Name','Device Product ID','Default Name' )     
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Bluetooth Paired'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Bluetooth Paired'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Bluetooth paired devices')
