import logging
import time

import click
import xleapp._version as version
import xleapp.app as app
import xleapp.helpers.descriptors as descriptors
import xleapp.helpers.utils as utils
import xleapp.templating as templating


logger_log = logging.getLogger("xleapp.logfile")

pass_application = click.make_pass_decorator(app.Application, ensure=True)


@click.command
@click.argument(
    "device_type",
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
@click.argument("artifacts", required=False, default=[])
@pass_application
def device(
    application: app.Application, device_type, input_path, output_folder, artifacts
):
    start_time = time.perf_counter()

    application.device.update({"Type": device_type})

    @descriptors.timed
    def process():
        logger_log.info(f"Processing {application.num_to_process} artifacts...")
        application.artifacts.run_queue()

    run_time, _ = process()
    logger_log.info(f"\nCompleted processing artifacts in {run_time:.2f}s")
    end_time = time.perf_counter()

    application.processing_time = end_time - start_time

    logger_log.info("\nGenerating index file...")
    templating.generate_index(application.app)
    logger_log.info("-> Index file generated!")

    application.generate_reports()


@click.command
@pass_application
def gui(application):
    """Runs xLEAPP into graphical mode"""
    import xleapp.gui as gui

    gui.main(application)


@click.command
@pass_application
def artifact_table(application: app.Application):
    application.generate_artifact_table()


@click.command
@pass_application
def artifact_path_lists(application: app.Application):
    application.generate_artifact_path_list


@click.group
@click.version_option(
    package_name=version.__project__.lower(),
    prog_name=version.__project__,
    version=version.__version__,
)
@pass_application
def cli(application: app.Application, artifact_table, artifact_paths_list):
    click.echo(
        utils.generate_program_header(
            f"{version.__project__} v{version.__version__}",
            application.input_path,
            application.report_folder,
            application.num_to_process,
            application.num_of_categories,
        ),
    )


cli.add_command(artifact_table)
cli.add_command(artifact_path_lists)
cli.add_command(device)
cli.add_command(gui)

if __name__ == "__main__":
    cli()
