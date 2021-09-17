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
        for key, val in pl.items():
            data_list.append((key, val))
            if key in ['ProductVersion', 'ProductBuildVersion', 'ProductName']:
                device_info.update({key: val})
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
        path, fp = self.found
        pl = plistlib.load(fp)
        for key, val in pl.items():
            if (
                isinstance(val, str)
                or isinstance(val, int)
                or isinstance(val, datetime.datetime)
            ):

                data_list.append((key, val))
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
                    device_info.update({key: val})

            elif key == "Installed Applications":
                data_list.append((key, ', '.join(val)))

        self.data = data_list
