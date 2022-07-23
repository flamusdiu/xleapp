import pytest


@pytest.fixture
def regex(request):
    from xleapp.artifacts.descriptors import SearchRegex

    class DummyClass:
        """Dummy class to assign the descriptor to.

        This also holds a lookup dictionary to check the set values against the
        values set with the object.
        """

        regex = SearchRegex()
        lookup = {}

    search = DummyClass()
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


@pytest.mark.parametrize(
    "regex",
    [
        [
            ("**/test.sqlite", "return_on_first_hit", "file_names_only"),
            ("**/test1.sqlite", "return_on_first_hit"),
            "**/test2.sqlite",
        ],
        [
            "**/test.sqlite",
            "**/test1.sqlite",
            "**/test2.sqlite",
        ],
        "**/myregex",
        [],
        pytest.param(["**/myregex"], marks=pytest.mark.xfail),
        pytest.param(2, marks=pytest.mark.xfail),
        pytest.param([2, "test", ("test", "test")], marks=pytest.mark.xfail),
    ],
    indirect=True,
)
class TestSearchRegexDescriptor:
    def test_tuples(self, regex):
        from xleapp.artifacts.regex import Regex

        assert isinstance(regex.regex, tuple)
        for search in regex.regex:
            assert isinstance(search, Regex)

    def test_return_value(self, regex):
        from xleapp.artifacts.regex import Regex

        for regex_search in regex.regex:
            assert isinstance(regex_search, Regex)
            assert regex_search.file_names_only == (
                "file_names_only" in regex.lookup[regex_search.regex]
            )

            assert regex_search.file_names_only == (
                "file_names_only" in regex.lookup[regex_search.regex]
            )

    def test_convert_to_string(self, regex):

        for regex_search in regex.regex:
            assert str(regex_search) == regex_search.regex

    def test_hash(self, regex):
        assert hash(regex.regex)
