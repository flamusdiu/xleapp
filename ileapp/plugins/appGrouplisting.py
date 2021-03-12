import pathlib
import plistlib
import sys
from dataclasses import dataclass

import biplist
from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class AppGroupListing(AbstractArtifact):

    def __post_init__(self):
        self.name = 'App Group Listing'
        self.description = ('List can included once installed but not present '
                            'apps. Each file is named .com.apple.mobile_'
                            'container_manager.metadata.plist')
        self.category = 'Installed Apps'
        self.report_headers = ('Bundle ID', 'Type', 'Directory GUID', 'Path')
        self.report_title = 'Bundle ID by AppGroup & PluginKit IDs'
        self.web_icon = Icon.PACKAGE

    @Search(
        '*/private/var/mobile/Containers/Shared/AppGroup/*/*.metadata.plist',
        '**/PluginKitPlugin/*.metadata.plist')
    @timed
    def process(self):
        data_list = []
        files_found = self.found

        print(files_found)
        print(f'regex: {self.regex}')
        exit(0)

        if isinstance(self.found, tuple):
            files_found = [self.found]

        for file_found in files_found:
            print(file_found)
            exit(0)
            path, fp = file_found
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

        self._data = data_list
