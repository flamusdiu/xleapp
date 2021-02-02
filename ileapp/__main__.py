import argparse
import logging

import ileapp.artifacts as artifacts
import ileapp.html_report as report
from ileapp import VERSION, __project__
import ileapp.globals
from ileapp.helpers import ValidateInput

logger = logging.getLogger(__name__)


def cli():
    """Main application entry point for CLI
    """

    installed_artifacts = {}

    for name in artifacts.artifact_list:
        installed_artifacts.update({name.lower(): name})

    parser = argparse.ArgumentParser(
        prog=__project__.lower(),
        description='iLEAPP: iOS Logs, Events, and Plists Parser.')
    parser.add_argument('-o', '--output_folder', required=False, action="store",
                        help='Output folder path')
    parser.add_argument('-i', '--input_path', required=False, action="store",
                        help='Path to input file/folder')
    parser.add_argument('--artifact', required=False, action="store",
                        help=(f'Filtered list of artifacts to run. '
                              f'Allowed: Core, '
                              f'{", ".join(list(installed_artifacts))}'),
                        metavar=None, nargs='*')
    parser.add_argument('-p', '--artifact_paths', required=False,
                        action="store_true",
                        help='Text file list of artifact paths')
    parser.add_argument('-l', '--artifact_table', required=False,
                        action='store_true',
                        help='Text file with table of artifacts')
    parser.add_argument('--gui', required=False, action="store_true",
                        help=f"Runs {__project__} into graphical mode")
    parser.add_argument('--version', action='version', version=VERSION)

    args = parser.parse_args()

    if args.artifact is None:
        # If no artifacts selected then choose all of them.
        [artifact.select_artifact(name) for name, artifact
            in artifacts.artifact_list.items()]
        core_artifacts_only = False
    else:
        args.artifact = [name.lower() for name in args.artifact]
        if args.artifact == ['core']:
            core_artifacts_only = True

        for name in args.artifact:
            try:
                if name.lower() != 'core':
                    artifacts.select_artifact(installed_artifacts[name.lower()])
            except KeyError:
                parser.error(f'Artifact ({name}) not installed or is unknown.')

    if args.gui:
        import ileapp.gui as gui

        gui.main()
    elif args.artifact_paths:
        artifacts.generate_artifact_path_list()
    elif args.artifact_table:
        artifacts.generate_artifact_table()
    else:
        input_path = args.input_path
        output_folder = args.output_folder

    extracttype, msg = ValidateInput(
        args.input_path,
        args.output_folder,
        artifacts.selected_artifacts,
        core_artifacts_only
    )

    if extracttype is None:
        parser.error(msg)
    else:
        ileapp.helpers.set_output_folder(output_folder)
        logger.info('Processing {len(args.artifact)} artifacts...')
        artifacts.crunch_artifacts(
            artifacts.selected_artifacts,
            extracttype,
            input_path,
            output_folder
        )


if __name__ == "__main__":
    cli()
