import importlib
import inspect
import io
import os
import pathlib
import traceback
from collections import OrderedDict, namedtuple
from textwrap import TextWrapper
from time import gmtime, process_time, strftime

import html_report
import prettytable
from helpers.ilapfuncs import is_platform_windows
from helpers.search_files import (FileSeekerDir, FileSeekerItunes,
                                  FileSeekerTar, FileSeekerZip)
from helpers.version_info import aleapp_version


def get_list_of_artifacts(ordered=True):
    """Generates a List of Artifacts installed

    Args
        ordered(bool): sets if the true order of the artifacts
            is return; otherwise returns certain artifacts
            at the beginning of the dict

    Returns:
        OrderedDict or dict: dictionary of artifacts with short names as keys
    """
    module_dir = pathlib.Path(importlib.util.find_spec(__name__).origin).parent
    artifact_list = OrderedDict() if ordered else {}

    # Setup named tuple to hold each artifact
    Artifact = namedtuple('Artifact', ['name', 'cls'])
    Artifact.__doc__ += ': Loaded forensic artifact'
    Artifact.cls.__doc__ = 'Artifact object class'
    Artifact.name.__doc__ = 'Artifact short name'

    for it in module_dir.glob('*.py'):
        if (it.suffix == '.py' and it.stem not in ['__init__']):

            module_name = f'{__name__}.{it.stem}'
            module = importlib.import_module(module_name)
            module_members = inspect.getmembers(module, inspect.isclass)
            print(module_members)
            for name, cls in module_members:
                if (not str(cls.__module__).endswith('Artifact')
                        and str(cls.__module__).startswith(__name__)):
                    print(name)
                    tmp_artifact = Artifact(name=cls().name, cls=cls())
                    artifact_list.update({name: tmp_artifact})

    # sort the artifact list
    tmp_artifact_list = sorted(list(artifact_list.items()))
    artifact_list.clear()
    artifact_list.update(tmp_artifact_list)

    return artifact_list


def generate_artifact_path_list():
    """Generates path file for usage with Autopsy
    """
    print('Artifact path list generation started.')
    print('')
    with open('path_list.txt', 'w') as paths:
        regex_list = []
        for key, value in get_list_of_artifacts(ordered=True).items():
            # Creates instance of each artifact class
            artifact = value['class']
            if isinstance(artifact.search_dirs, tuple):
                [regex_list.append(item) for item in artifact.search_dirs]
            else:
                regex_list.append(artifact.search_dirs)
        # Create a single list removing duplications
        ordered_regex_list = '\n'.join(set(regex_list))
        print(ordered_regex_list)
        paths.write(ordered_regex_list)
        print('')
        print('Artifact path list generation completed')


def generate_artifact_table():
    """Generates artifact list table.
    """
    headers = ["Short Name", "Full Name", "Search Regex"]
    wrapper = TextWrapper(expand_tabs=False,
                          replace_whitespace=False,
                          width=60)
    output_table = prettytable.PrettyTable(headers, align='l')
    output_table.hrules = prettytable.ALL
    print('Artifact table generation started.')
    print('')
    with open('artifact_table.txt', 'w') as paths:
        artifact_list = get_list_of_artifacts()
        for key, val in artifact_list.items():
            shortName = key
            fullName = val['class'].name
            searchRegex = val['class'].search_dirs
            if isinstance(searchRegex, tuple):
                searchRegex = '\n'.join(searchRegex)
            print(shortName)
            output_table.add_row([shortName,
                                  fullName,
                                  wrapper.fill(searchRegex)])
        paths.write(output_table.get_string(title='Artifact List',
                                            sortby='Short Name'))
    print('')
    print('Artifact table generation completed')


def crunch_artifacts(search_list, extracttype, input_path, out_params, ratio):
    """Processes all artifacts

    Args:
        search_list (dict): :obj:`dict` of Artifacts to process
        extracttype (str): type of file to process
        input_path (str): path to file
        out_params (OutputParams): object with output parameters
        ratio (int): progress bar percentage

    Returns:
        bool: Returns true/false on success/failure
    """
    start = process_time()

    logfunc('Procesing started. Please wait. This may take a few minutes...')

    logfunc('\n-------------------------------------------------'
            '-------------------------------------')
    logfunc(f'iLEAPP v{aleapp_version}: iLEAPP Logs,'
            f'Events, and Properties Parser')
    logfunc('Objective: Triage iOS Full System Extractions.')
    logfunc('By: Alexis Brignoni | @AlexisBrignoni | abrignoni.com')
    logfunc('By: Yogesh Khatri   | @SwiftForensics | swiftforensics.com')
    logdevinfo()

    seeker = None
    try:
        if extracttype == 'fs':
            seeker = FileSeekerDir(input_path)

        elif extracttype in ('tar', 'gz'):
            seeker = FileSeekerTar(input_path, out_params.temp_folder)

        elif extracttype == 'zip':
            seeker = FileSeekerZip(input_path, out_params.temp_folder)

        elif extracttype == 'itunes':
            seeker = FileSeekerItunes(input_path, out_params.temp_folder)

        else:
            logfunc('Error on argument -o (input type)')
            return False
    except Exception as ex:  # noqa
        logfunc('Had an exception in Seeker - see details below.'
                'Terminating Program!')
        temp_file = io.StringIO()
        traceback.print_exc(file=temp_file)
        logfunc(temp_file.getvalue())
        temp_file.close()
        exit(1)

    # Now ready to run
    logfunc(f'Artifact categories to parse: {str(len(search_list))}')
    logfunc(f'File/Directory selected: {input_path}')
    logfunc('\n--------------------------------------------'
            '------------------------------------------')

    log = open(os.path.join(out_params.report_folder_base, 'Script Logs',
               'ProcessedFilesLog.html'), 'w+', encoding='utf8')
    log.write(f'Extraction/Path selected: {input_path}<br><br>')

    categories_searched = 0
    # Special processing for iTunesBackup Info.plist as it is a
    # seperate entity, not part of the Manifest.db. Seeker won't find it
    if extracttype == 'itunes':
        info_plist_path = os.path.join(input_path, 'Info.plist')
        if os.path.exists(info_plist_path):
            artifact = search_list['ITunesBackupInfo']
            artifact.cls.process([info_plist_path],
                                 seeker, out_params.report_folder_base)
            # removing lastBuild as this takes its place
            del search_list['lastBuild']
        else:
            logfunc('Info.plist not found for iTunes Backup!')
            log.write('Info.plist not found for iTunes Backup!')
        categories_searched += 1
        # GuiWindow.SetProgressBar(categories_searched * ratio)

    # Search for the files per the arguments
    for name, artifact in search_list.items():
        search_regexes = []
        if (isinstance(artifact.cls.search_dirs, list)
                or isinstance(artifact.cls.search_dirs, tuple)):
            search_regexes = artifact.cls.search_dirs
        else:
            search_regexes.append(artifact.cls.search_dirs)
        files_found = []
        for artifact_search_regex in search_regexes:
            found = seeker.search(artifact_search_regex)
            if not found:
                logfunc()
                logfunc(f'No files found for {name} '
                        f'-> {artifact_search_regex}')
                log.write(f'No files found for {name} '
                          f'-> {artifact_search_regex}<br><br>')
            else:
                files_found.extend(found)
        if files_found:
            logfunc()
            artifact.cls.process(files_found, seeker,
                                 out_params.report_folder_base)
            for pathh in files_found:
                if pathh.startswith('\\\\?\\'):
                    pathh = pathh[4:]
                log.write(f'Files for {artifact_search_regex} located '
                          f'at {pathh}<br><br>')
        categories_searched += 1
        # GuiWindow.SetProgressBar(categories_searched * ratio)
    log.close()

    logfunc('')
    logfunc('Processes completed.')
    end = process_time()
    run_time_secs = end - start
    run_time_HMS = strftime('%H:%M:%S', gmtime(run_time_secs))
    logfunc("Processing time = {}".format(run_time_HMS))

    logfunc('')
    logfunc('Report generation started.')
    # remove the \\?\ prefix we added to input and output paths, so it does
    # not reflect in report
    if is_platform_windows():
        if out_params.report_folder_base.startswith('\\\\?\\'):
            out_params.report_folder_base = out_params.report_folder_base[4:]
        if input_path.startswith('\\\\?\\'):
            input_path = input_path[4:]
    html_report.generate_report(out_params.report_folder_base, run_time_secs,
                                run_time_HMS, extracttype, input_path)
    logfunc('Report generation Completed.')
    logfunc('')
    logfunc(f'Report location: {out_params.report_folder_base}')
    return True


def select_artifact(name):
    selected = props.artifact_list.pop(name, None)

    if selected is not None:
        props.selected_artifacts.update(selected)
