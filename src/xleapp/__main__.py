import argparse
import logging
import time

import xleapp.globals as g
import xleapp.log as log
import xleapp.report as report
import xleapp.templating as templating

from ._version import __project__, __version__
from .app import XLEAPP
from .artifacts import generate_artifact_path_list, generate_artifact_table
from .helpers.decorators import timed
from .helpers.search import search_providers
from .helpers.utils import ValidateInput, generate_program_header

logger_log = logging.getLogger("xleapp.logfile")


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
        help="parse Warrant Returns / User Generated Archives artifacts",
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
    group.add_argument(
        "--gui",
        required=False,
        action="store_true",
        help=f"Runs {__project__} into graphical mode",
    )
    parser.add_argument(
        "--version", action="version", version="f{__project__} v{__version__}"
    )

    return parser


def parse_args(parser):
    args = parser.parse_args()

    g.app = XLEAPP(
        output_folder=args.output_folder,
        input_path=args.input_path,
        device_type=args.device_type,
    )

    log.init()

    g.app.extraction_type = ValidateInput(
        args.input_path,
        args.output_folder,
        g.app.artifacts.selected,
    )

    # If an Itunes backup, use that artifact otherwise use
    # 'LastBuild' for everything else.
    if g.app.extraction_type == "itunes":
        g.app.artifacts.LAST_BUILD.value.selected = False
    else:
        g.app.artifacts.ITUNES_BACKUP_INFO.value.selected = False

    if args.artifact is None:
        # If no artifacts selected then choose all of them.
        g.app.artifacts.select_artifact(all_artifacts=True)
    else:
        filtered_artifacts = [
            name.lower() for name in args.artifact if name.lower() != "core"
        ]
        for name in filtered_artifacts:
            try:
                g.app.artifacts.select_artifact(name=name)
            except KeyError:
                g.app.error(f"Artifact ({name}) not installed " f" or is unknown.")

    if args.gui:
        import xleapp.gui as gui

        gui.main(g.app)
    elif args.artifact_paths:
        generate_artifact_path_list()
    elif args.artifact_table:
        generate_artifact_table()
    else:
        return args
    exit()


def _main(app: "XLEAPP"):

    start_time = time.perf_counter()

    print(
        generate_program_header(
            f"{__project__} v{__version__}",
            app.input_path,
            app.report_folder,
            app.num_to_process,
            app.num_of_categories,
        ),
    )

    app.seeker = search_providers.create(
        app.extraction_type.upper(),
        directory=app.input_path,
        temp_folder=app.temp_folder,
    )

    @timed
    def process():
        logger_log.info(f"Processing {app.num_to_process} artifacts...")

        app.crunch_artifacts()

    run_time, _ = process()

    logger_log.info(f"\nCompleted processing artifacts in {run_time:.2f}s")
    report.copy_static_files(app.report_folder)

    end_time = time.perf_counter()

    app.processing_time = end_time - start_time

    logger_log.info("\nGenerating index file...")
    templating.generate_index(app)
    logger_log.info("-> Index file generated!")

    app.generate_reports()


def cli():
    parser = get_parser()
    args = parse_args(parser)

    _main(g.app)


if __name__ == "__main__":
    cli()
