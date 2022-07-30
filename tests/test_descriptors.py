import re

import pytest
import xleapp.artifacts.descriptors as descriptors

from xleapp.artifacts.descriptors import FoundFiles, Icon, ReportHeaders
from xleapp.artifacts.regex import Regex
from xleapp.helpers.search import HandleValidator, InputPathValidation, PathValidator


@pytest.fixture
def regex_validator():
    from xleapp.artifacts.descriptors import SearchRegex

    class DummyClass:
        """Dummy class to assign the descriptor to.

        This also holds a lookup dictionary to check the set values against the
        values set with the object.
        """

        regex = SearchRegex()
        lookup = {}

    return DummyClass()


@pytest.fixture
def regex(request, regex_validator):

    search = regex_validator
    search.regex = request.param

    if isinstance(request.param, str):
        search.lookup.update({request.param: []})
    else:
        for regex_item in request.param:
            if isinstance(regex_item, tuple):
                search.lookup.update({regex_item[0]: regex_item[1:]})
            else:
                search.lookup.update({regex_item: []})

    return search


class TestValidatorABC:
    @pytest.fixture(scope="class", autouse=True)
    def test_validator(self):
        from xleapp.artifacts.descriptors import Validator

        class DummyValidator(Validator):
            default_value = 10

            def validator(self, value) -> None:
                if not isinstance(value, int):
                    raise TypeError(f"Expected {value!r} to be a int!.")

        class DummyClass:

            value = DummyValidator()

        return DummyClass

    def test_validator_creation(self, test_validator):
        from xleapp.helpers.descriptors import Validator

        assert test_validator, isinstance(Validator)

    @pytest.mark.parametrize("my_int, expected", [(None, 10), (42, 42)])
    def test_validator_default_value(self, test_validator, my_int, expected):

        test_obj = test_validator()
        test_obj.value = my_int
        assert test_obj.value == expected

    @pytest.mark.parametrize(
        "validator, my_args, message",
        [
            (FoundFiles, 42, "Expected 42 to be a set!"),
            (Icon, "Test", "Expected Test to be <enum 'WebIcon'>!"),
            (
                ReportHeaders,
                (42, 59, 100),
                "Expected (42, 59, 100) to be a list of tuples or tuple!",
            ),
            (PathValidator, False, "Expected Ellipsis to be a Path or Pathlike object"),
            (
                InputPathValidation,
                [42],
                "Expected [42] to be one of: str or Path.",
            ),
            (
                HandleValidator,
                42,
                "Expected 42 to be one of: string, Path, sqlite3.Connection or IOBase.",
            ),
        ],
    )
    def test_validator_types(self, validator, my_args, message):
        class DummyClass:
            value = validator()

        my_obj = DummyClass()

        with pytest.raises(TypeError, match=re.escape(message)):
            my_obj.value = my_args


@pytest.mark.parametrize(
    "regex, num",
    [
        (
            (
                ("**/test.sqlite", "return_on_first_hit", "file_names_only"),
                ("**/test1.sqlite", "return_on_first_hit"),
                "**/test2.sqlite",
            ),
            3,
        ),
        (
            (
                "**/test.sqlite",
                "**/test1.sqlite",
                "**/test2.sqlite",
            ),
            3,
        ),
        ("**/myregex", 1),
        ((), 0),
    ],
    indirect=["regex"],
)
class TestSearchRegexDescriptor:
    def test_tuples(self, regex, num):

        assert len(regex.regex) == num
        assert isinstance(regex.regex, tuple)
        for search in regex.regex:
            assert isinstance(search, Regex)

    def test_return_value(self, regex, num):

        for regex_search in regex.regex:
            assert isinstance(regex_search, Regex)
            assert regex_search.file_names_only == (
                "file_names_only" in regex.lookup[regex_search.regex]
            )

            assert regex_search.file_names_only == (
                "file_names_only" in regex.lookup[regex_search.regex]
            )

    def test_convert_to_string(self, regex, num):

        for regex_search in regex.regex:
            assert str(regex_search) == regex_search.regex

    def test_hash(self, regex, num):
        assert hash(regex.regex)


def test_search_descriptor_invalid_argument(regex_validator):

    with pytest.raises(
        TypeError,
        match=re.escape("Expected 42 to be a list of list or tuple of strings!"),
    ):
        regex_validator.regex = 42


class TestDescriptorRecursiveBoolReturn:
    bool_list = []

    def check_fct(self, fct):
        def wrapped(*args, **kwargs):
            if "bool_list" in kwargs:
                self.bool_list = kwargs["bool_list"]
            return fct(*args, **kwargs)

        return wrapped

    @pytest.mark.parametrize(
        "descriptor, test_strings, validation, results",
        [
            [descriptors.SearchRegex, ("**/regex", "**/regex2"), [True, True], True],
            [descriptors.SearchRegex, "**/regex", [], True],
            [
                descriptors.ReportHeaders,
                [("header1", "header2", "header2"), ("header3", "header4")],
                [True, True, True, True, True],
                True,
            ],
            [
                descriptors.ReportHeaders,
                ("header1", "header2", "header2"),
                [True, True, True],
                True,
            ],
            [descriptors.SearchRegex, (42, "**/regex"), [], False],
            [descriptors.SearchRegex, object(), [], False],
            [
                descriptors.ReportHeaders,
                [(42, 42), (object(), "header")],
                [],
                False,
            ],
            [
                descriptors.ReportHeaders,
                (42, "header2", object()),
                [],
                False,
            ],
            [descriptors.SearchRegex, ("**/regex", 42), [True], False],
            [
                descriptors.ReportHeaders,
                ("header2", object(), 42),
                [],
                False,
            ],
        ],
    )
    def test_recursion(self, monkeypatch, descriptor, test_strings, validation, results):
        with monkeypatch.context() as mp:
            mp.setattr(
                descriptor,
                "_check_list_of_tuples",
                self.check_fct(descriptor._check_list_of_tuples),
            )

            result = descriptor._check_list_of_tuples(test_strings)
            assert result == results
            assert self.bool_list == validation


class TestInputPathValidation:
    def test_str_input(self):
        from pathlib import Path

        ph = str(Path.cwd())

        class DummyClass:
            value = InputPathValidation()

        ph = Path.cwd()
        dummy_class = DummyClass()
        dummy_class.value = ph

        assert dummy_class.value == ("dir", ph.resolve())


def test_handle_validator_path():
    from pathlib import Path

    class DummyClass:
        value = HandleValidator()

    ph = Path.cwd()
    dummy_class = DummyClass()
    dummy_class.value = ph

    assert dummy_class.value is None
