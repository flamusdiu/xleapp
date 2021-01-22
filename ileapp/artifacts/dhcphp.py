from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import logfunc, tsv

import artifacts.artGlobals  # use to get iOS version -> iOSversion = artifacts.artGlobals.versionf

from artifacts.Artifact import AbstractArtifact


class DHCPHotspotClients(AbstractArtifact):

    _name = 'DHCP Hotspot Clients'
    _search_dirs = ('**/private/var/db/dhcpd_leases*')
    _report_section = 'DHCP'

    @staticmethod
    def get(files_found, report_folder, seeker):
        file_found = str(files_found[0])
        data_list = []
        reportval = ''
        with open(file_found, "r") as filefrom:
            for line in filefrom:
                cline = line.strip()
                if cline == "{":
                    reportval = reportval + ("<table><tr><td>Key</td><td>Values</td></tr>")
                elif cline == "}":
                    reportval = reportval + ("</table>")
                    data_list.append((reportval,))
                    reportval = ''
                # elif cline == '':
                # 	f.write('<br>')
                else:
                    ll = cline.split("=")
                    reportval = reportval + (f"<tr><td>{ll[0]}</td>")
                    reportval = reportval + (f"<td>{ll[1]}</td></tr>")

        if len(data_list) > 0:
            report = ArtifactHtmlReport('DHCP Hotspot Clients')
            report.start_artifact_report(report_folder, 'Hotspot Clients')
            report.add_script()
            data_headers = ('Hotspot Clients',)
            report.write_artifact_data_table(data_headers, data_list, file_found, html_escape=False)
            report.end_artifact_report()

            tsvname = 'DHCP Hotspot Clients'
            tsv(report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No data available')
