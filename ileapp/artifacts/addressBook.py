from ileapp.artifacts import AbstractArtifact
from ileapp.helpers.db import open_sqlite_db_readonly
from ileapp.html_report import Icon


class AddressBook(AbstractArtifact):

    _name = 'Address Book'
    _search_dirs = ('**/AddressBook.sqlitedb')
    _category = 'Address Book'
    _web_icon = Icon.BOOK_OPEN
    _report_headers = ('Contact ID', 'Contact Number', 'First Name',
                       'Middle Name', 'Last Name', 'Creation Date',
                       'Modification Date', 'Storage Place')

    def __init__(self, props):
        super().__init__(props)

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute(
            '''
            SELECT
            ABPerson.ROWID,
            VALUE,
            FIRST,
            MIDDLE,
            LAST,
            DATETIME(CREATIONDATE+978307200,'UNIXEPOCH'),
            DATETIME(MODIFICATIONDATE+978307200,'UNIXEPOCH'),
            NAME
            FROM ABPerson
            LEFT OUTER JOIN ABMultiValue ON ABPerson.ROWID = ABMultiValue.RECORD_ID
            LEFT OUTER JOIN ABStore ON ABPerson.STOREID = ABStore.ROWID
            '''
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                an = str(row[0])
                an = an.replace("b'", "")
                an = an.replace("'", "")
                data_list.append((an, row[1], row[2], row[3], row[4],
                                  row[5], row[6], row[7]))
            self.data = data_list

        db.close()
