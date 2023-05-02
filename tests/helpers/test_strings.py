import pytest

from xleapp.helpers.strings import print_str, raw, split_camel_case


@pytest.mark.parametrize(
    ["raw_bytes", "out_string"],
    [
        (
            b"\x74\x68\x65\x20\x64\x6f\x63\x74\x6f\x72\x20\x77\x61\x73\x20\x68\x65\x72\x65",
            "the doctor was here",
        ),
        (
            b"\x74\x68\x18\x20\x64\x6f\x15\x74\x6f\x72\x20\x77\x61\x73\x20\x03\x65\x72\x19",
            "th. do.tor was .er.",
        ),
    ],
)
def test_raw_strings(raw_bytes, out_string):
    raw_filtered = raw(raw_bytes)
    assert isinstance(raw_filtered, str)
    assert raw_filtered == out_string


@pytest.mark.parametrize(
    ["raw_bytes", "out_string"],
    [
        (
            b"\x74\x68\x65\x20\x64\x6f\x63\x74\x6f\x72\x20\x77\x61\x73\x20\x68\x65\x72\x65",
            "the doctor was here",
        ),
        (
            b"\x74\x68\x18\x20\x64\x6f\x15\x74\x6f\x72\x20\x77\x61\x73\x20\x03\x65\x72\x19",
            "th. do.tor was .er.",
        ),
    ],
)
def test_print_string(raw_bytes, out_string):
    filtered_string = print_str(raw_bytes)
    assert isinstance(filtered_string, filter)
    assert "".join(filtered_string) == out_string


def test_split_camel_case():
    bad_camel_case_string = 424242
    camel_case_string = "TheDoctorIsHere"

    with pytest.raises(TypeError):
        split_camel_case(bad_camel_case_string)

    assert split_camel_case(camel_case_string) == ["The", "Doctor", "Is", "Here"]
