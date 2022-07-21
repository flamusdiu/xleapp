from dataclasses import dataclass

import pytest

from xleapp import Artifact, Search, WebIcon
from xleapp.app import Application


@dataclass
class TestArtifact(Artifact):

    __test__ = False

    def __post_init__(self) -> None:
        self.name = "Accounts"
        self.category = "Accounts"
        self.web_icon = WebIcon.USER
        self.report_headers = (
            "Timestamp",
            "Account Desc.",
            "Username",
            "Description",
            "Identifier",
            "Bundle ID",
        )
        self.timeline = True

    @Search("**/Accounts3.sqlite")
    def process(self):
        for fp in self.found:
            cursor = fp().cursor()
            cursor.execute(
                """
                select
                datetime(zdate+978307200,'unixepoch','utc' ) as timestamp,
                zaccounttypedescription,
                zusername,
                zaccountdescription,
                zaccount.zidentifier,
                zaccount.zowningbundleid
                from zaccount, zaccounttype
                where zaccounttype.z_pk=zaccount.zaccounttype
                """,
            )

            all_rows = cursor.fetchall()
            if all_rows:
                for row in all_rows:
                    row_dict = dict_from_row(row)
                    self.data.append(tuple(row_dict.values()))


@dataclass
class TestArtifactMultipleSearch(Artifact):
    __test__ = False
    name = "TestArtifact"

    def __post_init__(self) -> None:
        self.name = "TestArtifact"
        self.category = "Test"
        self.web_icon = WebIcon.TRIANGLE

    @Search(
        "**/test.sqlite",
        "**/test1.sqlite",
        "**/test2.sqlite",
    )
    def process(self):
        pass


@dataclass
class TestArtifactMissingProcess(Artifact):
    __test__ = False

    def __post_init__(self) -> None:
        self.name = "TestArtifact"
        self.category = "Test"
        self.web_icon = WebIcon.TRIANGLE


@dataclass
class TestArtifactMultipleSearchWithOptions(Artifact):

    __test__ = False

    name = "TestArtifact"

    def __post_init__(self) -> None:
        self.name = "TestArtifact"
        self.category = "Test"
        self.web_icon = WebIcon.TRIANGLE

    @Search(
        ("**/test.sqlite", "return_on_first_hit", "file_names_only"),
        ("**/test1.sqlite", "return_on_first_hit"),
        "**/test2.sqlite",
    )
    def process(self):
        pass


@pytest.mark.parametrize(
    "artifact",
    [
        TestArtifact,
        TestArtifactMultipleSearch,
        TestArtifactMultipleSearchWithOptions,
        pytest.param(TestArtifactMissingProcess, marks=pytest.mark.xfail),
    ],
)
def test_create_artifact(artifact):
    assert isinstance(artifact(), Artifact)


@pytest.mark.parametrize(
    "artifact",
    [TestArtifact, TestArtifactMultipleSearch, TestArtifactMultipleSearchWithOptions],
)
def test_artifact_attach_app(artifact, app):
    artifact = artifact()
    artifact.app = app
    assert isinstance(artifact.app, Application)


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
)
class TestSearchRegexDescriptor:
    @pytest.mark.dependency()
    def test_tuples(self, regex):
        from xleapp.artifacts.descriptors import SearchRegex

        search = SearchRegex()
        try:
            search.validator(regex)
        except ValueError as exc:
            assert False, f"'search_regex_descriptor_tuples' raised an exception {exc}"

    @pytest.mark.dependency(depends=["test_tuples"])
    def test_return_value(self, regex):
        from xleapp.artifacts.descriptors import SearchRegex
        from xleapp.artifacts.regex import Regex

        class DummyClass:
            regex = SearchRegex()

        search = DummyClass()
        search.regex = regex

        regex_lookup = {k: v for k, *v in regex if isinstance(v, tuple)}

        for regex_search in search.regex:
            assert isinstance(regex_search, Regex)
            if regex_search.regex in regex_lookup:
                assert (
                    regex_search.file_names_only
                    == "file_names_only"
                    in regex_lookup[regex_search.regex]
                )

                assert (
                    regex_search.file_names_only
                    == "file_names_only"
                    in regex_lookup[regex_search.regex]
                )
