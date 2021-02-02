from dataclasses import dataclass

import ileapp.artifacts as artifacts
from ileapp.helpers.db import open_sqlite_db_readonly
from ileapp.html_report import Icon


@dataclass
class AggDictPasscodeType(artifacts.AbstractArtifact):

    name = 'Aggregate Dictionary Passcode Type'
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
