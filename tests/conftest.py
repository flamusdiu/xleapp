from contextlib import suppress
from pathlib import Path
from shutil import unpack_archive
import shutil

import pytest
import requests

from tqdm import tqdm

from xleapp.app import Application
from .test_artifacts import TestArtifact

ios_13_4_1_zip = (
    "https://digitalcorpora.s3.amazonaws.com/corpora/mobile/ios_13_4_1/ios_13_4_1.zip"
)

optional_markers = {
    "download": {
        "help": "downloads archives for tests. Greatly slows down tests!",
        "marker-descr": "downloads archives for testing. Tests will take longer!",
        "skip-reason": "Test only runs with the --{} option.",
    }
}


def pytest_addoption(parser):
    for marker, info in optional_markers.items():
        parser.addoption(
            "--{}".format(marker), action="store_true", default=False, help=info['help']
        )


def pytest_configure(config):
    for marker, info in optional_markers.items():
        config.addinivalue_line("markers", "{}: {}".format(marker, info['marker-descr']))


def pytest_collection_modifyitems(config, items):
    for marker, info in optional_markers.items():
        if not config.getoption("--{}".format(marker)):
            skip_test = pytest.mark.skip(reason=info['skip-reason'].format(marker))
            for item in items:
                if marker in item.keywords:
                    item.add_marker(skip_test)


@pytest.fixture(scope="session", autouse=True)
def test_data(request):
    return request.config.cache.makedir("test-data")


@pytest.mark.download
@pytest.fixture(scope="session", autouse=True)
def ios_image(test_data, request, pytestconfig):
    """Downloads and saves ios Image. Most test will use this file system image.
    This is extracted a head of time due to the overhead of trying to extract
    during testing.
    """

    # seems autouse always happens even if set to skip. This forces the skip.
    if not pytestconfig.getoption("--download"):
        return Path.cwd()

    fn = Path(test_data / "ios_13_4_1.zip")
    ios_file_extraction_root = test_data / "iOS 13.4.1 Extraction/Extraction"
    ios_file_sys = test_data / "13-4-1"

    request.config.cache.set("xleapp/ios-image-13-4-1", str(ios_file_sys))

    fn.touch(exist_ok=True)

    if fn.stat().st_size == 0:
        req = requests.get(ios_13_4_1_zip, stream=True)
        total_size = int(req.headers.get("content-length"))
        initial_pos = 0

        with fn.open(mode="b+a") as f:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=fn.name,
                initial=initial_pos,
                ascii=True,
            ) as progress_bar:
                for ch in req.iter_content(chunk_size=1024):
                    if ch:
                        f.write(ch)
                        progress_bar.update(len(ch))

    if not ios_file_extraction_root.exists():
        unpack_archive(str(fn), extract_dir=str(test_data))

    if not ios_file_sys.exists():
        # some files just do not extract
        with suppress(FileNotFoundError):
            unpack_archive(
                str(ios_file_extraction_root / "13-4-1.tar"),
                extract_dir=str(ios_file_sys),
            )

    # Return the file system directory after the second extraction
    return ios_file_sys


@pytest.fixture
def app(test_data, ios_image, mocker, monkeypatch):
    def fake_discover_plugins():
        plugins = mocker.MagicMock()
        plugins.plugins = [TestArtifact]
        return {'ios': {plugins}}

    monkeypatch.setattr(Application, "plugins", fake_discover_plugins())

    output_path = Path(test_data / "reports")
    output_path.mkdir(exist_ok=True)
    app = Application()

    yield app(device_type="ios", input_path=ios_image, output_path=output_path)
    
    shutil.rmtree(app.report_folder)


def test_app_input_path(ios_image, app):
    assert app.input_path == ios_image


def test_app_output_path(app, tmp_path_factory):
    assert app.output_path == tmp_path_factory / "data"
