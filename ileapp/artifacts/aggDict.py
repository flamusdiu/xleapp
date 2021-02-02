from dataclasses import dataclass

import ileapp.artifacts as artifacts 
from ileapp.helpers.db import open_sqlite_db_readonly
from ileapp.html_report import Icon


@dataclass
class AggDict(artifacts.AbstractArtifact):

    name = 'Aggregate Dictionary'
    search_dirs = ('*/AggregateDictionary/ADDataStore.sqlitedb')
    category = 'Aggregate Dictionary'
    web_icon = Icon.BOOK
    report_headers = ('Day', 'Key', 'Value', 'Seconds in Day Offset',
                       'Distribution Values Table ID')

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

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
