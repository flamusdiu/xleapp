import argparse
import logging

import xleapp.artifacts as artifacts
import xleapp.globals as g
import xleapp.log as log
import xleapp.report.html as html
import xleapp.report.templating as templating
from xleapp import VERSION, __project__
from xleapp.helpers.decorators import timed
from xleapp.helpers.search import search_providers
from xleapp.helpers.utils import ValidateInput

logger = logging.getLogger()

artifact_list = {}


def get_parser():
    parser = argparse.ArgumentParser(
        prog=__project__.lower(),
        description="xLEAPP: iOS Logs, Events, and Plists Parser.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-I",
        dest="device_type",
        action="store_const",
        const="ios",
        help="parse ios artifacts",
    )
    group.add_argument(
        "-R",
        dest="device_type",
        action="store_const",
        const="returns",
        help="parse warrenty return artifacts",
    )
    group.add_argument(
        "-A",
        dest="device_type",
        action="store_const",
        const="android",
        help="parse android artifacts",
    )
    group.add_argument(
        "-C",
        dest="device_type",
        action="store_const",
        const="chromebook",
        help="parse Chromebook artifacts",
    )
    group.add_argument(
        "-V",
        dest="device_type",
        action="store_const",
        const="vehicle",
        help="parse vehicle artifacts",
    )
    parser.add_argument(
        "-o",
        "--output_folder",
        required=False,
        action="store",
        help="Output folder path",
    )
    parser.add_argument(
        "-i",
        "--input_path",
        required=False,
        action="store",
        help="Path to input file/folder",
    )
    parser.add_argument(
        "--artifact",
        required=False,
        action="store",
        help=(
            "Filtered list of artifacts to run. "
            "Allowed: core, <check artifact list in documentation>"
        ),
        metavar=None,
        nargs="*",
    )
    parser.add_argument(
        "-p",
        "--artifact_paths",
        required=False,
        action="store_true",
        help="Text file list of artifact paths",
    )
    parser.add_argument(
        "-l",
        "--artifact_table",
        required=False,
        action="store_true",
        help="Text file with table of artifacts",
    )
    parser.add_argument(
        "--gui",
        required=False,
        action="store_true",
        help=f"Runs {__project__} into graphical mode",
    )
    parser.add_argument("--version", action="version", version=VERSION)

    return parser


def parse_args(parser):
    args = parser.parse_args()

    g.device.type = args.device_type

    if args.gui:
        import xleapp.gui as gui

        gui.main(artifact_list)
    elif args.artifact_paths:
        artifacts.generate_artifact_path_list()
    elif args.artifact_table:
        artifacts.generate_artifact_table()
    else:
        return args
    exit()


def _main(artifact_list: list, input_path, output_folder):

    extraction_type, msg = ValidateInput(
        input_path,
        output_folder,
        artifacts.selected(artifact_list),
    )

    if extraction_type is None:
        parser.error(msg)

    # If an Itunes backup, use that artifact otherwise use
    # 'LastBuild' for everything else.
    if extraction_type == "itunes":
        del artifact_list["lastbuild"]
    else:
        del artifact_list["itunesbackupinfo"]

    (report_folder, temp_folder, log_folder) = g.set_output_folder(output_folder)

    g.report_folder = report_folder

    num_to_process = len(
        {name for name, artifact in artifact_list.items() if artifact.selected}
    )
    num_of_categories = len(
        {
            artifact.category
            for _, artifact in artifact_list.items()
            if artifact.selected
        }
    )

    print(
        g.generate_program_header(
            input_path,
            report_folder,
            num_to_process,
            num_of_categories,
        ),
    )

    # Initalize logging
    log.init(
        log_folder,
        input_path,
        report_folder,
        num_to_process,
        num_of_categories,
    )

    # Initalizing templating for Reports
    templating.init(log_folder)

    g.seeker = search_providers.create(
        extraction_type.upper(),
        directory=input_path,
        temp_folder=temp_folder,
    )

    @timed
    def process():
        logger.info(
            f"Processing {num_to_process} artifacts...",
            extra={"flow": "no_filter"},
        )

        artifacts.crunch_artifacts(
            artifacts.selected(artifact_list),
            input_path,
        )

    run_time, _ = process()

    logger.info(
        f"Completed processing artifacts in {run_time:.2f}s",
        extra={"flow": "no_filter"},
    )
    html.copy_static_files()

    logger.info("Generating index file...", extra={"flow": "no_filter"})
    html.generate_index(
        artifact_list,
        report_folder,
        log_folder,
        extraction_type,
        processing_time=run_time,
    )
    logger.info("Index file generated!", extra={"flow": "no_filter"})

    logger.info("\nGenerating artifact html files ...", extra={"flow": "no_filter"})
    html.generate_artifacts(artifact_list, report_folder)
    logger.info("Finished generating html files!", extra={"flow": "no_filter"})


def cli(args):
    """Main application entry point for CLI"""

    input_path = args.input_path
    output_folder = args.output_folder

    if args.artifact is None:
        # If no artifacts selected then choose all of them.
        [artifacts.select(artifact_list, artifact) for artifact in artifacts.installed]
    else:
        filtered_artifacts = [
            name.lower() for name in args.artifact if name.lower() != "core"
        ]
        for name in filtered_artifacts:
            try:
                artifacts.select(artifact_list, name)
            except KeyError:
                logger.error(
                    f"Artifact ({name}) not installed " f" or is unknown.",
                    extra={"flow", "root"},
                )

    _main(artifact_list, input_path, output_folder)


if __name__ == "__main__":

    parser = get_parser()
    args = parse_args(parser)
    artifacts.build_artifact_list()
    for artifact in artifacts.installed:
        artifact_list.update({artifact: artifacts.services.create(artifact)})
    cli(args)
