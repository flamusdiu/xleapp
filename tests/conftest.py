from shutil import unpack_archive
from xleapp.app import Application

import pytest
import requests


ios_13_4_1_zip = (
    "https://digitalcorpora.s3.amazonaws.com/corpora/mobile/ios_13_4_1/ios_13_4_1.zip"
)


@pytest.fixture(scope="session")
def ios_image(tmp_path_factory):
    """Downloads and saves ios Image. Most test will use this file system image.
    This is extracted a head of time due to the overhead of trying to extract
    during testing.
    """
    r = requests.get(ios_13_4_1_zip, stream=True)
    fd = tmp_path_factory.mktemp("data")
    fn = fd / "ios_13_4_1.zip"
    fn.write_bytes(r)

    unpack_archive(str(fn), extract_dir=str(fd))

    ios_file_sys = fd / "iOS 13.4.1 Extraction" / "13-4-1.tar"
    unpack_archive(str(ios_file_sys), extract_dir=str(fd))

    # Return the file system directory after the second extraction
    return ios_file_sys

@pytest.fixture(scope="session")
def app():
    app = Application()