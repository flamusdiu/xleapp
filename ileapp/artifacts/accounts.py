from dataclasses import dataclass

import ileapp.artifacts.helpers.AbstractArtifact as ab
from ileapp.helpers.db import open_sqlite_db_readonly
from ileapp.html_report import Icon


@dataclass
class Accounts(ab.AbstractArtifact):

    def __post_init__(self):
        self.name = 'Accounts'
        self.search_dirs = '**/Accounts3.sqlite'
        self.category = 'Accounts'
        self.web_icon = Icon.USER
        self.report_headers = ('Timestamp', 'Account Desc.', 'Username',
                               'Description', 'Identifier', 'Bundle ID')

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute(
            """
            select
            datetime(zdate+978307200,'unixepoch','utc' ),
            zaccounttypedescription,
            zusername,
            zaccountdescription,
            zaccount.zidentifier,
            zaccount.zowningbundleid
            from zaccount, zaccounttype
            where zaccounttype.z_pk=zaccount.zaccounttype
            """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2],
                                  row[3], row[4], row[5]))
            self.data = data_list
