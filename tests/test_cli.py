import xleapp._version as version

from xleapp.helpers.utils import generate_program_header


def test_generate_program_header(app, capsys):
    print(
        generate_program_header(
            f"{version.__project__} v0.2.1",
            "C:\\4n6_output",
            "C:\\4n6_output\\report",
            app.num_to_process,
            app.num_of_categories,
        )
    )

    out, _ = capsys.readouterr()
    assert "xLEAPP" in out
    assert "0.2.1" in out
    assert "C:\\4n6_output" in out
    assert "C:\\4n6_output\\report" in out
    # TODO: Fix test. Failing when pushing to Github but passes locally.
    # assert "Artifacts to parse: 1 in 1 categories" in out
