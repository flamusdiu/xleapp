import importlib
import inspect
import io
import logging
import os
import traceback
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict, namedtuple
from pathlib import Path
from textwrap import TextWrapper

import ileapp.artifacts.helpers.AbstractArtifact as ab
import prettytable
from ileapp.helpers import is_platform_windows
from ileapp.helpers.decorators import timer
from ileapp.helpers.search_files import (FileSeekerDir, FileSeekerItunes,
                                         FileSeekerTar, FileSeekerZip)
from ileapp.html_report import Icon

logger = logging.getLogger(__name__)

# Setup named tuple to hold each artifact
Artifact = namedtuple('Artifact', ['name', 'cls'])
Artifact.__doc__ += ': Loaded forensic artifact'
Artifact.cls.__doc__ = 'Artifact object class'
Artifact.name.__doc__ = 'Artifact short name'


class Artifacts(OrderedDict):
    """List of artifacts installed
    """

    def __init__(self):
        super().__init__(self)

    def __setitem__(self, index, value) -> None:
        if isinstance(index, str) and isinstance(value, Artifact):
            super().__setitem__(index, value)
        else:
            raise TypeError(
                f"Error adding {{{str(index)}: {str(value)}}} to {self.name}! "
                f"Incorrect type for name or class not {type(Artifact)}"
            )

    def __str__(self) -> str:
        return f"Artifacts[{', '.join([name for name, artifact in self.items()])}]"


def _build_artifact_list() -> Artifacts:
    """Generates a List of Artifacts installed

    Returns:
        Artifacts: dictionary of artifacts with short names as keys
    """
    logger.debug('Generating artifact lists from file system...')
    module_dir = Path(importlib.util.find_spec(__name__).origin).parent
    artifact_list = Artifacts()

    for it in module_dir.glob('*.py'):
        if (it.suffix == '.py' and it.stem not in ['__init__']):

            module_name = f'{__name__}.{it.stem}'
            module = importlib.import_module(module_name)
            module_members = inspect.getmembers(module, inspect.isclass)
            for name, cls in module_members:
                if (not str(cls.__module__).endswith('Artifact')
                        and str(cls.__module__).startswith(__name__)
                        and not inspect.isabstract(cls)):

                    artifact_obj = cls()
                    tmp_artifact = Artifact(
                        cls=artifact_obj,
                        name=artifact_obj.name
                    )
                    artifact_list.update({name: tmp_artifact})

    # sort the artifact list
    tmp_artifact_list = sorted(list(artifact_list.items()))
    artifact_list.clear()
    artifact_list.update(tmp_artifact_list)

    logger.debug(f'Artifacts loaded: { len(artifact_list) }')
    return artifact_list


def generate_artifact_path_list(artifacts):
    """Generates path file for usage with Autopsy
    """
    logger.info('Artifact path list generation started.')

    with open('path_list.txt', 'w') as paths:
        regex_list = []
        for artifact in artifacts:
            if isinstance(artifact.search_dirs, tuple):
                [regex_list.append(item) for item in artifact.search_dirs]
            else:
                regex_list.append(artifact.search_dirs)
        # Create a single list removing duplications
        ordered_regex_list = '\n'.join(set(regex_list))
        logger.info(ordered_regex_list)
        paths.write(ordered_regex_list)

        logger.info('Artifact path list generation completed')


def build_search_regex_list(search_list) -> list:
    search_regexes = defaultdict(list)
    for name in search_list:
        artifact = props.installed_artifacts[name]
        if ((isinstance(artifact.cls.search_dirs, list)
                or isinstance(artifact.cls.search_dirs, tuple))
                and artifact.cls.core_artifact is False):
            for regex in artifact.cls.search_dirs:
                search_regexes[regex].append(name)
        else:
            search_regexes[artifact.cls.search_dirs].append(name)

    return search_regexes


def generate_artifact_table(artifacts):
    """Generates artifact list table.
    """
    headers = ["Short Name", "Full Name", "Search Regex"]
    wrapper = TextWrapper(expand_tabs=False,
                          replace_whitespace=False,
                          width=60)
    output_table = prettytable.PrettyTable(headers, align='l')
    output_table.hrules = prettytable.ALL
    output_file = Path('artifact_table.txt')

    logger.info('Artifact table generation started.')

    with open(output_file, 'w') as paths:
        for key, val in artifacts:
            shortName = key
            fullName = val.cls.name
            searchRegex = val.cls.search_dirs
            if isinstance(searchRegex, tuple):
                searchRegex = '\n'.join(searchRegex)
            output_table.add_row([shortName,
                                  fullName,
                                  wrapper.fill(searchRegex)])
        paths.write(output_table.get_string(title='Artifact List',
                                            sortby='Short Name'))
    logger.info(f'Table saved to: {output_file}')
    logger.info('Artifact table generation completed')


def crunch_core_artifacts(extracttype, seeker, input_path, output_folder):
    for name, artifact in props.core_artifacts.items():
        # Now ready to run
        # Special processing for iTunesBackup Info.plist as it is a
        # separate entity, not part of the Manifest.db. Seeker won't find it
        if name == 'ITunesBackupInfo':
            if extracttype == 'itunes':
                info_plist_path = input_path / 'Info.plist'
                if info_plist_path.exists():
                    artifact.cls.process([info_plist_path],
                                         seeker, output_folder)
                else:
                    logger.info('Info.plist not found for iTunes Backup!')
                # GuiWindow.SetProgressBar(categories_searched * ratio)
        else:
            for regex in [*artifact.cls.search_dirs]:
                found = seeker.search(regex)

                if found:
                    artifact.cls.files_found.extend(found)
                    logger.info(f'Files for {regex} located at {found}')

                    logger.info(f'Artifact {artifact.cls.category}[{name}] processing...')
                    process_time = artifact.cls.get(seeker)
                    artifact.cls.process_time = process_time
                    logger.info(f'Artifact {artifact.cls.category}[{name}] finished in {artifact.cls.process_time}')

                    if artifact.cls.report():
                        logger.info(f'Report generated for {artifact.cls.category}[{name}]')


artifact_list = _build_artifact_list()
