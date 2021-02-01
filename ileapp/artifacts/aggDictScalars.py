from dataclasses import dataclass

import ileapp.artifacts.helpers.AbstractArtifact as ab
from ileapp.helpers.db import open_sqlite_db_readonly
from ileapp.html_report import Icon


@dataclass
class AggDictScalars(ab.AbstractArtifact):

    name = 'Aggregate Dictionary Scalars'
    search_dirs = ('*/AggregateDictionary/ADDataStore.sqlitedb')
    category = 'Aggregate Dictionary'
    web_icon = Icon.BOOK

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute(
            """
            select
            date(dayssince1970*86400, 'unixepoch'),
            key,
            value
            from
            scalars
            """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2]))

            self.data = data_list
