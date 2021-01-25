import plistlib

from helpers.ilapfuncs import tsv
from html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport

from artifacts.Artifact import AbstractArtifact


class DHCPReceivedList(AbstractArtifact):

    _name = 'DHCP Received List'
    _search_dirs = ('**/private/var/db/dhcpclient/leases/en*')
    _category = 'DHCP'
    _web_icon = Icon.SETTINGS

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        data_list = []
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                if key == "IPAddress":
                    data_list.append((key, val))
                if key == "LeaseLength":
                    data_list.append((key, val))
                if key == "LeaseStartDate":
                    data_list.append((key, val))
                if key == "RouterHardwareAddress":
                    data_list.append((key, val))
                if key == "RouterIPAddress":
                    data_list.append((key, val))
                if key == "SSID":
                    data_list.append((key, val))

        if len(data_list) > 0:
            report = ArtifactHtmlReport('DHCP Received List')
            report.start_artifact_report(report_folder, 'Received List')
            report.add_script()
            data_headers = ('Key', 'Value')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'DHCP Received List'
            tsv(report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No data available')
