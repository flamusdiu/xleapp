import plistlib

import blackboxprotobuf
from helpers import tsv
from ileapp.html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport

from artifacts.Artifact import AbstractArtifact


class AppleMapsApplication(ab.AbstractArtifact):
    _name = 'Apple Maps Application'
    _search_dirs = ('**/Data/Application/*/Library/Preferences/com.apple.Maps.plist')
    _category = 'Locations'
    _web_icon = Icon.MAP_PIN

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        file_found = str(files_found[0])

        with open(file_found, 'rb') as f:
            plist = plistlib.load(f)

            types = {'1': {'type': 'double', 'name': 'Latitude'},
                     '2': {'type': 'double', 'name': 'Longitude'},
                     '3': {'type': 'double', 'name': ''},
                     '4': {'type': 'fixed64', 'name': ''},
                     '5': {'type': 'double', 'name': ''}
                     }
            protobuf = plist.get('__internal__LastActivityCamera', None)
            if protobuf:
                internal_plist, di = blackboxprotobuf.decode_message(protobuf,
                                                                     types)
                latitude = (internal_plist['Latitude'])
                longitude = (internal_plist['Longitude'])

                data_list = []
                data_list.append((latitude, longitude))
                report = ArtifactHtmlReport('Apple Maps App')
                report.start_artifact_report(report_folder, 'Apple Maps App')
                report.add_script()
                data_headers = ('Latitude', 'Longitude' )
                report.write_artifact_data_table(data_headers, data_list,
                                                 file_found)
                report.end_artifact_report()

                tsvname = 'Apple Maps Application'
                tsv(report_folder, data_headers, data_list, tsvname)
