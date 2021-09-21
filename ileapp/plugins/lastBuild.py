import datetime
import plistlib
from dataclasses import dataclass

import ileapp.ilapglobals as g
from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, core_artifact, timed


@core_artifact
@dataclass
class LastBuild(AbstractArtifact):
    def __post_init__(self):
        self.name = 'Last Build'
        self.category = 'IOS Build'
        self.generate_report = False

    @timed
    @Search('*LastBuildInfo.plist')
    def process(self):
        data_list = []
        device_info = g.device
        fp = self.found
        pl = plistlib.load(fp)
        for key, value in pl.items():
            data_list.append((key, value))
            if key in ['ProductVersion', 'ProductBuildVersion', 'ProductName']:
                device_info.update({key: value})
        self.data = data_list


@core_artifact
@dataclass
class ITunesBackupInfo(AbstractArtifact):
    def __post_init__(self):
        self.name = 'iTunesBackup'
        self.category = 'IOS Build'
        self.generate_report = False

    @timed
    @Search('*LastBuildInfo.plist')
    def process(self):
        data_list = []
        device_info = g.device
        fp = self.found
        pl = plistlib.load(fp)
        for key, value in pl.items():
            if (
                isinstance(value, str)
                or isinstance(value, int)
                or isinstance(value, datetime.datetime)
            ):

                data_list.append((key, value))
                if key in (
                    'Build Version',
                    'Device Name',
                    'ICCID',
                    'IMEI',
                    'Last Backup Date',
                    'MEID',
                    'Phone Number',
                    'Product Name',
                    'Product Type',
                    'Product Version',
                    'Serial Number',
                ):
                    device_info.update({key: value})

            elif key == "Installed Applications":
                data_list.append((key, ', '.join(value)))

        self.data = data_list
