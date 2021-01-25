import pathlib
import plistlib
import sys

import biplist
from helpers.ilapfuncs import tsv
from html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport

from artifacts.Artifact import AbstractArtifact


class AppGroupListing(AbstractArtifact):

    _name = 'App Group Listing'
    _search_dirs = (('*/private/var/mobile/Containers/Shared/AppGroup/*/*'
                    '.metadata.plist'),
                    '**/PluginKitPlugin/*.metadata.plist')
    _category = 'Installed Apps'
    _web_icon = Icon.PACKAGE

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        data_list = []
        for file_found in files_found:
            with open(file_found, "rb") as fp:
                if sys.version_info >= (3, 9):
                    plist = plistlib.load(fp)
                else:
                    plist = biplist.readPlist(fp)

            bundleid = plist['MCMMetadataIdentifier']

            p = pathlib.Path(file_found)
            appgroupid = p.parent.name
            fileloc = str(p.parents[1])
            typedir = str(p.parents[1].name)

            data_list.append((bundleid, typedir, appgroupid, fileloc))

        if len(data_list) > 0:
            filelocdesc = 'Path column in the report'
            description = ('List can included once installed but not present '
                           'apps. Each file is named .com.apple.mobile_'
                           'container_manager.metadata.plist')
            report = ArtifactHtmlReport('Bundle ID by AppGroup '
                                        '& PluginKit IDs')
            report.start_artifact_report(report_folder,
                                         ('Bundle ID by AppGroup'
                                          '& PluginKit IDs'), description)
            report.add_script()
            data_headers = ('Bundle ID', 'Type', 'Directory GUID', 'Path')
            report.write_artifact_data_table(data_headers, data_list,
                                             filelocdesc)
            report.end_artifact_report()

            tsvname = 'Bundle ID - AppGroup ID - PluginKit ID'
            tsv(report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No data on Bundle ID - AppGroup ID - PluginKit ID')
