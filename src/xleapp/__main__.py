from __future__ import annotations

import argparse
import logging
import time

import xleapp.globals as g
import xleapp.log as log
import xleapp.templating as templating

from ._version import __project__, __version__
from .app import Application
from .artifacts import generate_artifact_path_list, generate_artifact_table
from .helpers.decorators import timed
from .helpers.utils import generate_program_header


logger_log = logging.getLogger("xleapp.logfile")


def get_parser() -> argparse.ArgumentParser:
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
        "--artifacts",
        required=False,
        action="store",
        help=(
            "Filtered list of artifacts to run. "
            "Allowed: core, <check artifact list in documentation>"
        ),
        metavar=None,
        nargs="+",
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
        "--version",
        action="version",
        version="f{__project__} v{__version__}",
    )

    return parser


def parse_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    args = parser.parse_args()
    artifacts = args.artifacts or ()
    g.app = Application()

    if args.gui:
        import xleapp.gui as gui

        gui.main(g.app)
    elif args.artifact_paths:
        generate_artifact_path_list(artifacts)
    elif args.artifact_table:
        generate_artifact_table(artifacts)
    else:
        g.app(
            *artifacts,
            device_type=args.device_type,
            output_path=args.output_folder,
            input_path=args.input_path,
        )
        return args
    exit()


def _main(app: Application) -> None:

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

    @timed
    def process():
        logger_log.info(f"Processing {app.num_to_process} artifacts...")
        app.crunch_artifacts(thread=None, window=None)

    run_time: float
    run_time, _ = process()
    logger_log.info(f"\nCompleted processing artifacts in {run_time:.2f}s")
    end_time = time.perf_counter()

    app.processing_time = end_time - start_time

    logger_log.info("\nGenerating index file...")
    templating.generate_index(app)
    logger_log.info("-> Index file generated!")

    app.generate_reports()


def cli() -> None:
    parser = get_parser()
    parse_args(parser)

    log.init()

    _main(g.app)


if __name__ == "__main__":
    cli()
