from dataclasses import dataclass

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class AggDictPasscodeType(AbstractArtifact):
    def __post_init__(self):
        self.name = 'Aggregate Dictionary Passcode Type'
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
            case
            when value=-1 then '6-digit'
            when value=0 then 'no passcode'
            when value=1 then '4-digit'
            when value=2 then 'custom alphanumeric'
            when value=3 then 'custom numeric'
            else "n/a"
            end "value"
            from
            scalars
            where key like 'com.apple.passcode.passcodetype%'
            """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)

        if usageentries > 0:
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2]))

            self.data = data_list
