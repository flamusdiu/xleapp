import plistlib

from ileapp.artifacts import AbstractArtifact
from ileapp.html_report import Icon


class AccountConfiguration(AbstractArtifact):

    _name = 'Account Configuration'
    _search_dirs = ('**/com.apple.accounts.exists.plist')
    _category = 'Accounts'
    _web_icon = Icon.USER

    def __init__(self, props):
        super().__init__(props)

    def get(self, seeker):
        data_list = []
        file_found = self.files_found
        with open(file_found, "rb") as fp:
            pl = plistlib.load(fp)
            for key, val in pl.items():
                data_list.append((key, val))

        self.data = data_list
