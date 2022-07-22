from dataclasses import dataclass
from multiprocessing import dummy

import pytest

from xleapp import Artifact, Search, WebIcon
from xleapp.app import Application
from xleapp.artifacts.descriptors import SearchRegex
from xleapp.artifacts.regex import Regex


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
class TestArtifactCreation:
    def test_create_artifact(self, artifact):
        assert isinstance(artifact(), Artifact)

    def test_artifact_attach_app(self, artifact, app):
        test_artifact = artifact()
        test_artifact.app = app
        assert isinstance(test_artifact.app, Application)

@pytest.fixture
def regex(request):
        from xleapp.artifacts.descriptors import SearchRegex
        from xleapp.artifacts.regex import Regex

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
    indirect=True
)
class TestSearchRegexDescriptor:  
    def test_tuples(self, regex):
        assert isinstance(regex.regex, tuple)
        for search in regex.regex:
            assert isinstance(search, Regex)

    def test_return_value(self, regex):
        for regex_search in regex.regex:
            assert isinstance(regex_search, Regex)
            assert (
                regex_search.file_names_only
                == ("file_names_only"
                in regex.lookup[regex_search.regex])
            )

            assert (
                regex_search.file_names_only
                == ("file_names_only"
                in regex.lookup[regex_search.regex])
            )
    
    def test_convert_to_string(self, regex):

        for regex_search in regex.regex:
            assert str(regex_search) == regex_search.regex
        
    def test_hash(self, regex):
        assert hash(regex.regex)
