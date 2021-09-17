import plistlib
from dataclasses import dataclass
from datetime import datetime

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class VoiceRecording(AbstractArtifact):
    def __post_init__(self):
        self.name = 'Voice Recordings'
        self.category = 'Voice-Recordings'
        self.report_headers = ('Creation Date', 'Title', 'Path to File', 'Audio File')
        self.report_title = 'Voice Recordings'
        self.web_icon = Icon.MIC

    @timed
    @Search(
        '**/Recordings/*.composition/manifest.plist',
        '**/Recordings/*.m4a',
        file_names_only=True,
    )
    def process(self):
        data_list = []
        plist_files = []
        m4a_files = []

        for file_found in self.found:
            if file_found.suffix('.plist'):
                plist_files.append(file_found)
            elif file_found.suffix('.m4a'):
                m4a_filename = file_found
                if ' ' in m4a_filename:
                    m4a_filename = m4a_filename.replace(' ', '_')
                m4a_files.append(m4a_files)
                self.copyfile(file_found, m4a_filename)

        plist_files.sort()
        m4a_files.sort()

        for plist_file, m4a_file in zip(plist_files, m4a_files):
            with open(plist_file, "rb") as file:
                pl = plistlib.load(file)
                ct = unix_epoch_to_readable_date(pl['RCSavedRecordingCreationTime'])

                audio = (
                    '<audio controls>'
                    f'<source src="{m4a_file}" type="audio/wav">'
                    '<p>Your browser does not support HTML5'
                    'audio elements.</p></audio>'
                )

                data_list.append(
                    (
                        ct,
                        pl['RCSavedRecordingTitle'],
                        pl['RCComposedAVURL'].split('//')[1],
                        audio,
                    )
                )

        self.data = data_list


def unix_epoch_to_readable_date(unix_epoch_time):
    unix_time = float(unix_epoch_time + 978307200)
    readable_time = datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
    return readable_time
