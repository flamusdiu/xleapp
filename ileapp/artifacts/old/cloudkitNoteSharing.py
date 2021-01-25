import io
import os

import nska_deserialize as nd
from html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport
from helpers.ilapfuncs import tsv
from helpers.db import open_sqlite_db_readonly

from artifacts.Artifact import AbstractArtifact


class CloudKitNotSharing(AbstractArtifact):

    _name = 'CloudKit Note Sharing'
    _search_dirs = ('*NoteStore.sqlite*')
    _category = 'CloudKit'
    _web_icon = Icon.SHARE_2

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        for file_found in files_found:
            file_found = str(file_found)

            if file_found.endswith('NoteStore.sqlite'):
                db = open_sqlite_db_readonly(file_found)
                cursor = db.cursor()
                cursor.execute('''
                select z_pk, zserverrecorddata
                from
                ziccloudsyncingobject
                where
                zserverrecorddata not null
                ''')

                note_data = []
                all_rows = cursor.fetchall()
                result_number = len(all_rows)
                if result_number > 0:

                    for row in all_rows:

                        filename = os.path.join(report_folder, 'zserverrecorddata_'+str(row[0])+'.bplist')
                        output_file = open(filename, "wb")
                        output_file.write(row[1])
                        output_file.close()

                        deserialized_plist = nd.deserialize_plist(io.BytesIO(row[1]))
                        creator_id = ''
                        last_modified_id = ''
                        creation_date = ''
                        last_modified_date = ''
                        last_modified_device = ''
                        record_type = ''
                        record_id = ''
                        for item in deserialized_plist:
                            if 'RecordCtime' in item:
                                creation_date = item['RecordCtime']
                            elif 'RecordMtime' in item:
                                last_modified_date = item['RecordMtime']
                            elif 'LastModifiedUserRecordID' in item:
                                last_modified_id = item['LastModifiedUserRecordID']['RecordName']
                            elif 'CreatorUserRecordID' in item:
                                creator_id = item['CreatorUserRecordID']['RecordName']
                            elif 'ModifiedByDevice' in item:
                                last_modified_device = item['ModifiedByDevice']
                            elif 'RecordType' in item:
                                record_type = item['RecordType']
                            elif 'RecordID' in item:
                                record_id = item['RecordID']['RecordName']

                        note_data.append([record_id, record_type, creation_date, creator_id, last_modified_date, last_modified_id, last_modified_device])

                    description = ('CloudKit Note Sharing - Notes information '
                                   'shared via CloudKit. Look up the '
                                   'Record ID in the ZICCLOUDSYYNCINGOBJECT.'
                                   'ZIDENTIFIER column.')
                    report = ArtifactHtmlReport('Note Sharing')
                    report.start_artifact_report(report_folder, 'Note Sharing', description)
                    report.add_script()
                    note_headers = ('Record ID', 'Record Type', 'Creation Date', 'Creator ID', 'Modified Date', 'Modifier ID', 'Modifier Device')
                    report.write_artifact_data_table(note_headers, note_data, file_found)
                    report.end_artifact_report()

                    tsvname = 'CloudKit Note Sharing'
                    tsv(report_folder, note_headers, note_data, tsvname)
                else:
                    logfunc('No CloudKit - CloudKit Note Sharing data available')

                db.close()
