import pathlib
from typing import Generator

from xleapp.helpers.filetype import _NUM_SIGNATURE_BYTES, get_signature_bytes, signature


def test_get_sigature_types(
    file_type_test_files: Generator[pathlib.Path, None, None]
) -> None:
    file: pathlib.Path = next(file_type_test_files)
    result: bytes = get_signature_bytes(file)
    assert len(result) == _NUM_SIGNATURE_BYTES


def test_signature_bytes(single_file_signature: bytes) -> None:
    signature_100_bytes: bytes = single_file_signature[:100]
    signature_num_signature_bytes: bytes = single_file_signature[:_NUM_SIGNATURE_BYTES]

    result_signature: bytes = signature(single_file_signature[:100])
    assert len(result_signature) == 100
    assert len(result_signature) < _NUM_SIGNATURE_BYTES
    assert result_signature == signature_100_bytes

    result_signature: bytes = signature(single_file_signature)
    assert len(result_signature) == _NUM_SIGNATURE_BYTES
    assert result_signature == signature_num_signature_bytes
