import logging
import time

import click
import xleapp._version as version
import xleapp.app as app
import xleapp.globals as g
import xleapp.helpers.decorators as decorators
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
@click.argument("artifacts", required=False, nargs=-1)
@pass_application
def device(
    application: app.Application,
    device_type: str,
    input_path: click.Path,
    output_folder: click.Path,
    artifacts: list,
):
    """Parses the selected device

    Args:
        application (app.Application): Application object
        device_type (str): device to parse
        input_path (click.Path): path to the input folder/file
        output_folder (click.Path): path to the output folder to create the report
        artifacts (list): list of artifacts to parse. Default: All
    """
    start_time = time.perf_counter()

    application.set_device_type(device_type)
    application = application(output_folder, input_path)

    if len(artifacts) == 0:
        for artifact in application.artifacts:
            if artifact.device == device_type:
                application.artifacts.toggle_artifact(artifact.cls_name)
    else:
        for artifact in artifacts:
            application.artifacts.toggle_artifact(artifact)

    @decorators.timed
    def process():
        logger_log.info(f"Processing {application.num_to_process} artifacts...")
        application.artifacts.run_queue()

    run_time, _ = process()
    logger_log.info(f"\nCompleted processing artifacts in {run_time:.2f}s")
    end_time = time.perf_counter()

    application.processing_time = end_time - start_time

    logger_log.info("\nGenerating index file...")
    templating.generate_index(application)
    logger_log.info("-> Index file generated!")

    application.generate_reports()


@click.command
@pass_application
def gui(application: app.Application):
    """Runs the GUI interface

    Args:
        application (app.Application):
    """
    import xleapp.gui as gui

    gui.main(application)


@click.command
@pass_application
def artifact_table(application: app.Application):
    """Prints out a file containing all the artifacts and regexes

    Args:
        application (app.Application): Application object
    """
    application.generate_artifact_table()
    click.echo("Saved artifact table as `artifact_table.txt` in current directory!")


@click.command
@pass_application
def artifact_path_lists(application: app.Application):
    """Prints out a file containing a list of regexes usable by Autopsy

    Args:
        application (app.Application): Application object
    """
    application.generate_artifact_path_list()
    click.echo("Saved artifact path list for Autopsy!")


@click.group
@click.version_option(
    package_name=version.__project__.lower(),
    prog_name=version.__project__,
    version=version.__version__,
)
@pass_application
def cli(application: app.Application):
    g.app = application
    current_ctx = click.get_current_context()

    if current_ctx.invoked_subcommand in ["artifact-table", "artifact-path-lists"]:
        num_of_installed_or_process = len(application.artifacts.installed())
        num_of_installed_or_process_categories = len(
            application.artifacts.installed_categories()
        )

    else:
        num_of_installed_or_process = application.num_to_process
        num_of_installed_or_process_categories = application.num_of_categories

    click.echo(
        utils.generate_program_header(
            f"{version.__project__} v{version.__version__}",
            application.input_path,
            application.report_folder,
            num_of_installed_or_process,
            num_of_installed_or_process_categories,
        ),
    )


cli.add_command(artifact_table)
cli.add_command(artifact_path_lists)
cli.add_command(device)
cli.add_command(gui)

if __name__ == "__main__":
    cli()
