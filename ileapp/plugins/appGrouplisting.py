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
        self.description = (
            'List can included once installed but not present '
            'apps. Each file is named .com.apple.mobile_'
            'container_manager.metadata.plist'
        )
        self.category = 'Installed Apps'
        self.report_headers = ('Bundle ID', 'Type', 'Directory GUID', 'Path')
        self.report_title = 'Bundle ID by AppGroup & PluginKit IDs'
        self.web_icon = Icon.PACKAGE

    @timed
    @Search(
        '*/private/var/mobile/Containers/Shared/AppGroup/*/*.metadata.plist',
        '**/PluginKitPlugin/*.metadata.plist',
    )
    def process(self):
        data_list = []

        for fp in self.found:
            if sys.version_info >= (3, 9):
                plist = plistlib.load(fp)
            else:
                plist = biplist.readPlist(fp)

            bundleid = plist['MCMMetadataIdentifier']

            p = pathlib.Path(fp.name)
            appgroupid = p.parent.name
            fileloc = p.parent
            typedir = p.parents[1].name

            data_list.append((bundleid, typedir, appgroupid, fileloc))

        self.data = data_list
