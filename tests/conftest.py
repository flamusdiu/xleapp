import pathlib
from typing import Generator

import pytest

from xleapp.helpers.filetype import _NUM_SIGNATURE_BYTES


@pytest.fixture(scope="function")
def file_type_test_files() -> Generator[pathlib.Path, None, None]:
    path = pathlib.Path(__file__).parent
    data = path / "data_filetypes"

    return data.glob("*")


@pytest.fixture
def single_file_signature() -> bytes:
    path = pathlib.Path(__file__).parent
    data = path / "data_filetypes" / "file_example_JPG_100kB.jpg"

    with data.open("rb") as fp:
        return bytes(fp.read(_NUM_SIGNATURE_BYTES))
