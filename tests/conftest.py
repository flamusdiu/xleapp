from shutil import unpack_archive
from pathlib import Path
from contextlib import suppress

import pytest
import requests
from tqdm import tqdm


ios_13_4_1_zip = (
    "https://digitalcorpora.s3.amazonaws.com/corpora/mobile/ios_13_4_1/ios_13_4_1.zip"
)


def fake_discover_plugins(mocker):
    plugins = mocker.MagicMock()
    plugins.plugins = set('Accounts')
    return {'xleapp-ios', plugins}


@pytest.fixture(scope="session")
def ios_image(request):
    """Downloads and saves ios Image. Most test will use this file system image.
    This is extracted a head of time due to the overhead of trying to extract
    during testing.
    """
    fd: Path = request.config.cache.makedir("test-data")
    fn = Path(fd / "ios_13_4_1.zip")
    ios_file_extraction_root = fd / "iOS 13.4.1 Extraction/Extraction"
    ios_file_sys = fd / "13-4-1"

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
        unpack_archive(str(fn), extract_dir=str(fd))

    if not ios_file_sys.exists():
        # some files just do not extract
        with suppress(FileNotFoundError):
            unpack_archive(
                str(ios_file_extraction_root / "13-4-1.tar"),
                extract_dir=str(ios_file_sys),
            )

    # Return the file system directory after the second extraction
    return ios_file_sys


@pytest.fixture(scope="session")
def app(request, ios_image):
    from xleapp.app import Application
    import xleapp.helpers.utils as utils

    pytest.MonkeyPatch.setattr(utils, "discovered_plugins", fake_discover_plugins)

    app = Application()
    output_path = request.config.cache.makedir("test-data/reports")

    app(device_type="ios", input_path=ios_image, output_path=output_path)
    return app


def test_app_input_path(ios_image, app):
    assert app.input_path == ios_image


def test_app_output_path(ios_image, app, tmp_path_factory):
    assert app.output_path == tmp_path_factory / "data"
