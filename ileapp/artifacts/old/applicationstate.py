import io

import nska_deserialize as nd
from helpers import tsv
from helpers.db import open_sqlite_db_readonly
from ileapp.html_report import Icon
from html_report.artifact_report import ArtifactHtmlReport

from artifacts.Artifact import AbstractArtifact


class ApplicationState(ab.AbstractArtifact):

    _name = 'Application State'
    _search_dirs = ('**/applicationState.db')
    _category = 'Installed Apps'
    _web_icon = Icon.PACKAGE

    def __init__(self):
        super().__init__(self)

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        select ait.application_identifier as ai, kvs.value as compat_info,
        (SELECT kvs.value from kvs left join application_identifier_tab on application_identifier_tab.id = kvs.application_identifier
        left join key_tab on kvs.key = key_tab.id
        WHERE key_tab.key='XBApplicationSnapshotManifest' and kvs.key = key_tab.id
        and application_identifier_tab.id = ait.id
        ) as snap_info
        from kvs
        left join application_identifier_tab ait on ait.id = kvs.application_identifier
        left join key_tab on kvs.key = key_tab.id
        where key_tab.key='compatibilityInfo'
        order by ait.id
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            snap_info_list = []
            for row in all_rows:
                # bundleid = str(row[0])
                plist_file_object = io.BytesIO(row[1])
                try:
                    plist = nd.deserialize_plist(plist_file_object)

                    if type(plist) is dict:
                        var1 = plist.get('bundleIdentifier', '')
                        var2 = plist.get('bundlePath', '')
                        var3 = plist.get('sandboxPath', '')
                        data_list.append((var1, var2, var3))
                        if row[2]:
                            snap_info_list.append((var1, var2, var3, row[2]))
                    else:
                        logfunc(f'For {row[0]} Unexpected type '
                                f'{str(type(plist))} found as plist '
                                f'root, can\'t process')
                except (nd.DeserializeError,
                        nd.biplist.NotBinaryPlistException,
                        nd.biplist.InvalidPlistException,
                        nd.ccl_bplist.BplistError,
                        ValueError, TypeError, OSError, OverflowError) as ex:
                    logfunc(f'Failed to read plist for {row[0]}, error was: '
                            f'{str(ex)}')

            report = ArtifactHtmlReport('Application State')
            report.start_artifact_report(report_folder, 'Application State DB')
            report.add_script()
            data_headers = ('Bundle ID', 'Bundle Path', 'Sandbox Path')
            report.write_artifact_data_table(data_headers, data_list,
                                             file_found)
            report.end_artifact_report()

            tsvname = 'Application State'
            tsv(report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No Application State data available')

        db.close()
