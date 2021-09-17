import plistlib
from dataclasses import dataclass

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class AccountConfiguration(AbstractArtifact):
    def __post_init__(self):
        self.name = 'Account Configuration'
        self.category = 'Accounts'
        self.web_icon = Icon.USER

    @timed
    @Search('**/com.apple.accounts.exists.plist')
    def process(self):
        data_list = []

        fp = self.found
        pl = plistlib.load(fp)
        for key, val in pl.items():
            data_list.append((key, val))

        self.data = data_list
