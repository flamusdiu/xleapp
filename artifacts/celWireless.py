import os
import plistlib
import sqlite3

from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import is_platform_windows, logdevinfo, logfunc, tsv

from .Artifact import AbstractArtifact


class CellularWireless(AbstractArtifact):

    _name = 'Cellular Wireless'
    _search_dirs = ('*wireless/Library/Preferences/com.apple.*')
    _report_section = 'Cellular Wireless'

    @staticmethod
    def get(files_found, report_folder, seeker):
        data_list = []
        for filepath in files_found:
            basename = os.path.basename(filepath)
            if (
                basename == "com.apple.commcenter.device_specific_nobackup.plist"
                or basename == "com.apple.commcenter.plist"
            ):
                p = open(filepath, "rb")
                plist = plistlib.load(p)
                for key, val in plist.items():
                    data_list.append((key, val, filepath))
                    if key == "ReportedPhoneNumber":
                        logdevinfo(f"Reported Phone Number: {val}")
                    
                    if key == "CDMANetworkPhoneNumberICCID":
                        logdevinfo(f"CDMA Network Phone Number ICCID: {val}")
                    
                    if key == "imei":
                        logdevinfo(f"IMEI: {val}")
                        
                    if key == "LastKnownICCID":
                        logdevinfo(f"Last Known ICCID: {val}")
                    
                    if key == "meid":
                        logdevinfo(f"MEID: {val}")
        
        
        
        location = 'see source field'
        report = ArtifactHtmlReport('Cellular Wireless')
        report.start_artifact_report(report_folder, 'Cellular Wireless')
        report.add_script()
        data_headers = ('Key','Values', 'Source' )     
        report.write_artifact_data_table(data_headers, data_list, location)
        report.end_artifact_report()
        
        tsvname = 'Cellular Wireless'
        tsv(report_folder, data_headers, data_list, tsvname)

