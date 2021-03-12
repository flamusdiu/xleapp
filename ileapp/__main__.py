import argparse
from collections import defaultdict
import logging

import ileapp.artifacts as artifacts
import ileapp.globals as g
import ileapp.report.html as html
from ileapp import VERSION, __project__
from ileapp.helpers.decorators import timed
from ileapp.helpers.search import search_providers
from ileapp.helpers.utils import ValidateInput
from ileapp.log import init_logging
from ileapp.report.templating import init_jinja

logger = logging.getLogger()


def get_parser():
    parser = argparse.ArgumentParser(
        prog=__project__.lower(),
        description='iLEAPP: iOS Logs, Events, and Plists Parser.')
    parser.add_argument('-o', '--output_folder', required=False, action="store",
                        help='Output folder path')
    parser.add_argument('-i', '--input_path', required=False, action="store",
                        help='Path to input file/folder')
    parser.add_argument('--artifact', required=False, action="store",
                        help=(f'Filtered list of artifacts to run. '
                              f'Allowed: core, '
                              f'{", ".join(artifacts.installed)}'),
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

    return parser


def parse_args(parser):
    args = parser.parse_args()
    if args.gui:
        import ileapp.gui as gui

        gui.main()
    elif args.artifact_paths:
        artifacts.generate_artifact_path_list()
        exit(0)
    elif args.artifact_table:
        artifacts.generate_artifact_table()
        exit(0)
    else:
        return args


@timed
def _main(artifact_list,
          report_folder,
          extraction_type,
          input_path,
          temp_folder):

    g.seeker = search_providers.create(
        extraction_type.upper(),
        directory=input_path,
        temp_folder=temp_folder)

    artifacts.crunch_artifacts(
        artifacts.selected(artifact_list),
        input_path,
        report_folder,
        temp_folder
    )


def cli():
    """Main application entry point for CLI
    """

    parser = get_parser()
    args = parse_args(parser)
    input_path = args.input_path
    output_folder = args.output_folder
    core_artifacts_only = False

    artifact_list = {}
    for artifact in artifacts.installed:
        artifact_list.update({artifact: artifacts.services.create(artifact)})

    if args.artifact is None:
        # If no artifacts selected then choose all of them.
        [artifacts.select(artifact_list, artifact) for artifact
            in artifacts.installed]
    else:
        filtered_artifacts = [name.lower() for name in args.artifact
                              if name.lower() != 'core']
        if len(filtered_artifacts) == 0:
            core_artifacts_only = True
        else:
            for name in filtered_artifacts:
                try:
                    artifacts.select(artifact_list, name)
                except KeyError:
                    logger.error(f'Artifact ({name}) not installed '
                                 f' or is unknown.', extra={'flow', 'root'})

    extraction_type, msg = ValidateInput(
        input_path,
        output_folder,
        artifacts.selected(artifact_list),
        core_artifacts_only
    )

    if extraction_type is None:
        parser.error(msg)
    else:

        # If an Itunes backup, use that artifact otherwise use
        # 'LastBuild' for everything else.
        if extraction_type == 'itunes':
            del artifact_list['lastbuild']
        else:
            del artifact_list['itunesbackupinfo']

        (report_folder,
         temp_folder,
         log_folder,
         temp_folder) = g.set_output_folder(output_folder)

        g.report_folder = report_folder

        num_to_process = 0
        artifact_categories = defaultdict(list)
        for name, artifact in artifact_list.items():
            if artifact.selected:
                artifact_categories[artifact.category] = name
                num_to_process += 1
        num_of_cateorgies = len(artifact_categories)
        print(g.generate_program_header(input_path,
                                        num_to_process, num_of_cateorgies))

        init_logging(log_folder, input_path,
                     num_to_process, num_of_cateorgies)
        init_jinja(log_folder)

        logger.info(f'Processing {num_to_process} artifacts...',
                    extra={'flow': 'no_filter'})

        timed, value = _main(artifact_list, report_folder, extraction_type,
                             input_path, temp_folder)

        logger.info(f'Completed processing artifacts in {timed:.2f}s',
                    extra={'flow': 'no_filter'})
        html.copy_static_files(report_folder)

        logger.info('Generating index file...', extra={'flow': 'no_filter'})
        html.generate_index(
            report_folder,
            log_folder,
            extraction_type,
            processing_time=timed
        )
        logger.info('Index file generated!', extra={'flow': 'no_filter'})


if __name__ == "__main__":
    cli()
