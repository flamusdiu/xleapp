import plistlib

from ileapp.html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport
from helpers import tsv

from artifacts.Artifact import AbstractArtifact


class CacheRoutesGmap(ab.AbstractArtifact):

    _name = 'Google Maps Cache Routes'
    _search_dirs = ('**/Library/Application Support/CachedRoutes/*.plist')
    _category = 'Locations'
    _web_icon = Icon.MAP_PIN

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        data_list = []
        for file_found in files_found:
            file_found = str(file_found)

            with open(file_found, 'rb') as f:
                deserialized = plistlib.load(f)
                length = len(deserialized['$objects'])
                for x in range(length):
                    try:
                        lat = deserialized['$objects'][x]['_coordinateLat']
                        lon = deserialized['$objects'][x]['_coordinateLong']  # lat longs
                        data_list.append((file_found, lat, lon))
                    except:  # noqa
                        pass

        if len(data_list) > 0:
            description = 'Google Maps Cache Routes'
            report = ArtifactHtmlReport('Locations')
            report.start_artifact_report(report_folder, 'Google Maps Cache Routes', description)
            report.add_script()
            data_headers = ('Source File','Latitude','Longitude' )
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Google Maps Cache Routes'
            tsv(report_folder, data_headers, data_list, tsvname)
