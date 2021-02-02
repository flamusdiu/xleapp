import plistlib
from dataclasses import dataclass

import ileapp.artifacts as artifacts
from ileapp.html_report import Icon


@dataclass
class AccountConfiguration(artifacts.AbstractArtifact):

    name = 'Account Configuration'
    search_dirs = ('**/com.apple.accounts.exists.plist')
    category = 'Accounts'
    web_icon = Icon.USER

    def get(self, seeker):
        data_list = []
        file_found = self.files_found
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                data_list.append((key, val))

        self.data = data_list
