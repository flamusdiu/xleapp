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

    @Search(["**/test.sqlite"],["**/test1.sqlite"],["**/test2.sqlite"])
    def process(self):
        pass

@dataclass
class TestArtifactMissingProcess(Artifact):
    __test__ = False
    def __post_init__(self) -> None:
        self.name = "TestArtifact"
        self.category = "Test"
        self.web_icon = WebIcon.TRIANGLE


@pytest.fixture
def test_artifact():
    return TestArtifact


@pytest.mark.parametrize(
    "artifact",
    [
        TestArtifact,
        TestArtifactMultipleSearch,
        pytest.param(TestArtifactMissingProcess, marks=pytest.mark.xfail),
    ],
)
def test_create_artifact(artifact):
    assert isinstance(artifact(), Artifact)


@pytest.mark.parametrize(
    "artifact",
    [TestArtifact, TestArtifactMultipleSearch],
)
def test_artifact_attach_app(artifact, app):
    artifact = artifact()
    artifact.app = app
    assert isinstance(artifact.app, Application)
