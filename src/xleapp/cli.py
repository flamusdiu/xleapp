import logging
import time

from email.policy import default

import click
import xleapp._version as version
import xleapp.helpers.descriptors as descriptors
import xleapp.helpers.utils as utils
import xleapp.templating as templating


logger_log = logging.getLogger("xleapp.logfile")


@click.command
@click.argument(
    "type",
    type=click.Choice(
        ["ios", "returns", "android", "chromebook", "vehicle"], case_sensitive=False
    ),
)
@click.option(
    "--output_folder",
    "-o",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True, writable=True),
    help="output folder path",
)
@click.option(
    "--input_path",
    "-i",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True, writable=True),
    help="input file/folder path",
)
@click.argument(
    "artifacts",
    required=False,
)
def device():
    pass


@click.command
def gui():
    """Runs xLEAPP into graphical mode"""
    import xleapp.gui as gui

    gui.main()


@click.command
def main(ctx) -> None:

    ctx.app = ctx.with_resource(Application())
    start_time = time.perf_counter()

    @descriptors.timed
    def process():
        logger_log.info(f"Processing {ctx.app.num_to_process} artifacts...")
        ctx.app.artifacts.run_queue()

    run_time, _ = process()
    logger_log.info(f"\nCompleted processing artifacts in {run_time:.2f}s")
    end_time = time.perf_counter()

    ctx.app.processing_time = end_time - start_time

    logger_log.info("\nGenerating index file...")
    templating.generate_index(ctx.app)
    logger_log.info("-> Index file generated!")

    ctx.app.generate_reports()


@click.group
@click.option(
    "-l", "--artifact-table", is_flag=True, help="prints table of artifacts and regexes"
)
@click.option(
    "-p",
    "--artifact-paths-list",
    is_flag=True,
    help="prints regexes for use with Autopsy",
)
@click.version_option(
    package_name=version.__project__.lower(),
    prog_name=version.__project__,
    version=version.__version__,
)
def cli(artifact_table, artifact_paths_list):
    click.echo(
        utils.generate_program_header(
            f"{version.__project__} v{version.__version__}",
            ctx.app.input_path,
            ctx.app.report_folder,
            ctx.app.num_to_process,
            ctx.app.num_of_categories,
        ),
    )


cli.add_command(device)
cli.add_command(gui)
click.make_pass_decorator(Application())

if __name__ == "__main__":
    cli()
