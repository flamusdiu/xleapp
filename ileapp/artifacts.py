import importlib
import inspect
import logging
from collections import UserDict
from pathlib import Path
from textwrap import TextWrapper
from typing import Dict, List, Type

import prettytable

from ileapp.abstract import AbstractArtifact

logger = logging.getLogger(__name__)

__all__ = [
    'generate_artifact_table',
    'generate_artifact_path_list',
    'crunch_artifacts',
    'select',
    'services',
    'installed'
]


class ArtifactServiceBuilder:
    _instance: Type[AbstractArtifact] = None

    def __call__(self,
                 artifact: Type[AbstractArtifact]
                 ) -> Type[AbstractArtifact]:
        if not self._instance:
            self._instance = artifact
        return self._instance


class ArtifactService(UserDict):
    def __init__(self) -> None:
        self.data = {}
        self._items = 0

    def __len__(self) -> int:
        return self._items

    def register_builder(self,
                         key: str,
                         builder: ArtifactServiceBuilder
                         ) -> None:
        self._items = self._items + 1
        self.data[key] = builder

    def create(self, key: str) -> Type[AbstractArtifact]:
        builder = self.data.get(key)
        if not builder:
            raise ValueError(key)

        return builder()


def _build_artifact_list():
    """Generates a List of Artifacts installed

    Returns:
        Artifacts: dictionary of artifacts with short names as keys
    """

    artifacts = ArtifactService()
    installed = []

    logger.debug('Generating artifact lists from file system...',
                 extra={'flow': 'no_filter'})
    module_dir = Path(
        importlib.util.find_spec(__name__).origin).parent / 'plugins'
    for it in module_dir.glob('*.py'):
        if (it.suffix == '.py' and it.stem not in ['__init__']):
            module_name = f'{".".join(module_dir.parts[-2:])}.{it.stem}'
            module = importlib.import_module(module_name, inspect.isfunction)
            module_members = inspect.getmembers(module, inspect.isclass)
            for name, cls in module_members:
                # check MRO (Method Resolution Order) for
                # AbstractArtifact classes. Also, insure
                # we do not get an abstract class.
                if (len(set([str(name).find('AbstractArtifact')
                             for name in cls.mro()]) - set([-1])) != 0
                        and not inspect.isabstract(cls)):
                    builder = ArtifactServiceBuilder()
                    artifacts.register_builder(
                        name.lower(),
                        builder(cls))
                    installed.append(name.lower())

    logger.debug(f'Artifacts loaded: {len(artifacts)}')
    return artifacts, installed


services, installed = _build_artifact_list()


def crunch_artifacts(
        artifact_list,
        input_path,
        report_folder_base,
        temp_folder) -> bool:

    core_artifacts = {}
    selected_artifacts = {}

    for name, artifact in artifact_list:
        if artifact.core:
            core_artifacts.update({name: artifact})
        elif artifact.selected:
            selected_artifacts.update({name: artifact})

    if len(core_artifacts) > 0:
        _crunch_core_artifacts(
            core_artifacts,
            input_path,
            report_folder_base)

    if len(selected_artifacts) > 0:
        _crunch_selected_artifacts(
            selected_artifacts,
            report_folder_base
        )


def _crunch_selected_artifacts(
        artifacts,
        report_folder_base) -> bool:

    for name, artifact in artifacts.items():
        _process_artifact(name, artifact)
        _gen_report(name, artifact, report_folder_base)


def _crunch_core_artifacts(artifacts,
                           input_path,
                           report_folder):

    for name, artifact in artifacts.items():
        # Now ready to run
        # Special processing for iTunesBackup Info.plist as it is a
        # separate entity, not part of the Manifest.db. Seeker won't find it
        if name == 'ITunesBackupInfo':
            info_plist_path = Path(input_path) / 'Info.plist'
            if info_plist_path.exists():
                _process_artifact(name, artifact)
                _gen_report(name, artifact, report_folder)
            else:
                logger.info('Info.plist not found for iTunes Backup!',
                            extra={'flow': 'no_filter'})
            # GuiWindow.SetProgressBar(categories_searched * ratio)
        else:
            _process_artifact(name, artifact)
            _gen_report(name, artifact, report_folder)


def _process_artifact(name: str,
                      artifact: Type[AbstractArtifact]) -> None:
    logger.info(
        f'\n{artifact.category} [{name}] artifact '
        f'processing...', extra={'flow': 'no_filter'})
    process_time, value = artifact.process()

    for regex, files_found in artifact.regex:
        logger.info(
            f'\nFiles for {regex} located at:', extra={'flow': 'process_file'}
        )
        [logger.info(f'\t{file}', extra={'flow': 'process_file'})
            for file in files_found]

    artifact.process_time = process_time
    logger.info(
        f'{artifact.category} [{name}] artifact '
        f'finished in {process_time:.2f}s',
        extra={'flow': 'no_filter'})


def _gen_report(name: str,
                artifact: Type[AbstractArtifact],
                output_folder) -> None:
    if artifact.report(output_folder):
        logger.info(f'Report generated for '
                    f'{artifact.category} [{name}]\n',
                    extra={'flow': 'no_filter'})


def selected(artifacts: Dict[str, object]) -> List:
    return [(name, artifact) for name, artifact
            in artifacts.items() if (artifact.selected or artifact.core)]


def select(artifacts: List[AbstractArtifact],
           name: str = None,
           all_artifacts: bool = False,
           long_running_process: bool = False,
           reset: bool = False) -> None:
    """Toggles if an artifact should be run

       Core artifacts cannot be toggled. `all_artifacts` will not select any
       artifact marked as long running unless it also is set to True.

       If you want to ensure the state of the artifacts, call this with
       `reset=True` to reset all the states to their default values.

    Args:
        artifacts(List[object]): installed list of artifacts
        name (str, optional): short name of the artifact. Defaults to None.
        all_artifacts (bool, optional): bool to select all artifacts.
            Defaults to False.
        long_running_process (bool, optional): used with `all_artifacts`
            to select long running processes. Defaults to False.
        reset (bool, optional): clears the select flags on non-core artifacts.
            Defaults to True.
    """
    if reset:
        # resets all artifacts to be not selected
        for name, artifact in artifacts.items():
            selected = artifact.selected
            lrp = artifact.long_running_process
            core = artifact.core
            if not core:
                artifact.selected = False
    elif name is None and all_artifacts:
        for name, artifact in artifacts.items():
            selected = artifact.selected
            lrp = artifact.long_running_process
            core = artifact.core
            if lrp and not core:
                if long_running_process:
                    artifact.selected = not selected
            elif not core:
                artifact.selected = not selected
    elif not artifacts.get(name).core:
        selected = artifacts.get(name).selected
        artifacts.get(name).selected = not selected


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


def generate_artifact_table(artifacts) -> None:
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
    logger.info(f'Table saved to: {output_file}', extra={'flow': 'no_flter'})
    logger.info('Artifact table generation completed',
                extra={'flow': 'no_filter'})
