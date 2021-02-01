import datetime
import plistlib
from dataclasses import dataclass

from ileapp.artifacts.helpers.AbstractArtifact import (AbstractArtifact,
                                                       core_artifact)


@core_artifact
@dataclass
class LastBuild(AbstractArtifact):

    def __post_init__(self):
        self.name = 'Last Build'
        self.search_dirs = '*LastBuildInfo.plist'
        self.category = 'IOS Build'
        self.generate_report = False

    def get(self, seeker):
        data_list = []
        device_info = {}
        file_found = self.files_found
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                data_list.append((key, val))
                if key in ['ProductVersion',
                           'ProductBuildVersion',
                           'ProductVersion']:
                    device_info.update({key: val})

        if device_info:
            self.props.device_info(**device_info)

        self.data = data_list


@core_artifact
@dataclass
class ITunesBackupInfo(AbstractArtifact):
    name = 'iTunesBackup'
    search_dirs = '*LastBuildInfo.plist'
    category = 'IOS Build'
    generate_report = False

    def get(self, seeker):
        data_list = []
        device_info = {}
        file_found = self.files_found
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                if (isinstance(val, str)
                        or isinstance(val, int)
                        or isinstance(val, datetime.datetime)):

                    data_list.append((key, val))
                    if key in ('Build Version', 'Device Name', 'ICCID', 'IMEI',
                               'Last Backup Date', 'MEID', 'Phone Number',
                               'Product Name', 'Product Type',
                               'Product Version', 'Serial Number'):
                        device_info.update({key: val})

                elif key == "Installed Applications":
                    data_list.append((key, ', '.join(val)))

        self.data = data_list
        self.props.device_info(**device_info)
