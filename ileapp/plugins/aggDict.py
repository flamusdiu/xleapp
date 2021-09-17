from dataclasses import dataclass

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class AggDict(AbstractArtifact):
    def __post_init__(self):
        self.name = 'Aggregate Dictionary'
        self.category = 'Aggregate Dictionary'
        self.web_icon = Icon.BOOK
        self.report_headers = (
            'Day',
            'Key',
            'Value',
            'Seconds in Day Offset',
            'Distribution Values Table ID',
        )

    @timed
    @Search('*/AggregateDictionary/ADDataStore.sqlitedb')
    def process(self):
        fp = self.found
        cursor = fp.cursor()

        cursor.execute(
            """
            select
            date(distributionkeys.dayssince1970*86400, 'unixepoch'),
            distributionkeys.key,
            distributionvalues.value,
            distributionvalues.secondsindayoffset,
            distributionvalues.distributionid
            from
            distributionkeys, distributionvalues
            where distributionkeys.rowid = distributionvalues.distributionid
            """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4]))

        self.data = data_list
