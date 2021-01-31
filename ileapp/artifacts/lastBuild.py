import datetime
import plistlib

from ileapp.artifacts import AbstractArtifact


class LastBuild(AbstractArtifact):

    _name = 'Last Build'
    _search_dirs = '*LastBuildInfo.plist'
    _category = 'IOS Build'
    _core_artifact = True
    _report_headers = ('Key', 'Values')
    _generate_report = False

    def __init__(self, props):
        super().__init__(props)

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


class ITunesBackupInfo(AbstractArtifact):
    _name = 'iTunesBackup'
    _search_dirs = '*LastBuildInfo.plist'
    _category = 'IOS Build'
    _core_artifact = True
    _generate_report = False

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
