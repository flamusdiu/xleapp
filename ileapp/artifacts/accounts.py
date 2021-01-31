from ileapp.artifacts import AbstractArtifact
from ileapp.helpers.db import open_sqlite_db_readonly
from ileapp.html_report import Icon


class Accounts(AbstractArtifact):

    _name = 'Accounts'
    _search_dirs = ("**/Accounts3.sqlite")
    _category = 'Accounts'
    _web_icon = Icon.USER
    _report_headers = ('Timestamp', 'Account Desc.', 'Username',
                       'Description', 'Identifier', 'Bundle ID')

    def __init__(self, props):
        super().__init__(props)

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
