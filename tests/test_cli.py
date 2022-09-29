from xleapp._version import __project__, __version__
from xleapp.helpers.utils import generate_program_header


def test_get_project_name(app, capsys):
    generate_program_header(
        f"{__project__} v{__version__}",
        app.input_path,
        app.report_folder,
        app.num_to_process,
        app.num_of_categories,
    )

    out, err = capsys.readouterr()
    assert f"{__project__}" in out
    assert f"{__version__}" in out
    assert f"{app.input_path}" in out
    assert f"{app.report_folder}" in out
    assert f"{app.num_to_process}" in out
    assert f"{app.num_of_categories}" in out
