from xleapp._version import __project__, __version__
from xleapp.helpers.utils import generate_program_header


def test_generate_program_header(app, capsys):
    print(
        generate_program_header(
            f"{__project__} v{__version__}",
            app.input_path,
            app.report_folder,
            app.num_to_process,
            app.num_of_categories,
        )
    )

    out, _ = capsys.readouterr()
    assert f"{__project__}" in out
    assert f"{__version__}" in out
    assert f"{app.input_path}" in out
    assert f"{app.report_folder}" in out
    assert "Artifacts to parse: 2 in 1 categories" in out
