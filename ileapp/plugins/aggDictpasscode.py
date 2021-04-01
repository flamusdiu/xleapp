from dataclasses import dataclass

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class AggDictPasscode(AbstractArtifact):

    def __post_init__(self):
        self.name = "Aggregate Dictionary Passcode State"
        self.category = 'Aggregate Dictionary'
        self.web_icon = Icon.BOOK

    @timed
    @Search('*/AggregateDictionary/ADDataStore.sqlitedb')
    def process(self):
        fp = self.found
        cursor = fp.cursor()

        cursor.execute(
            """
            select
            date(dayssince1970*86400, 'unixepoch'),
            key,
            value
            from
            scalars
            where key like 'com.apple.passcode.numpasscode%'
            """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2]))

            self.data = data_list
