import pytest
from dataclasses import dataclass
from xleapp import Artifact, Search, WebIcon, artifacts
from xleapp.app import Application


@dataclass
class TestArtifact(Artifact):
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

    @Search("Accounts__Accounts", "**/Accounts3.sqlite")
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
    name = "TestArtifact"

    def __post_init__(self) -> None:
        self.name = "TestArtifact"
        self.category = "Test"
        self.web_icon = WebIcon.TRIANGLE

    @Search("TestArtifact__Unknown", "**/test.sqlite")
    @Search("TestArtifact__Unknown", "**/test1.sqlite")
    @Search("TestArtifact__Unknown", "**/test2.sqlite")
    def process(self):
        pass


@dataclass
class TestArtifactMissingProcess(Artifact):
    def __post_init__(self) -> None:
        self.name = "TestArtifact"
        self.category = "Test"
        self.web_icon = WebIcon.TRIANGLE


@pytest.fixture
def test_artifact():
<<<<<<< HEAD
=======
    class Accounts(Artifact):
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

    return Accounts


@pytest.fixture
def test_artifact_multiple_search():
    class TestArtifact(Artifact):
        name = "TestArtifact"

        def __post_init__(self) -> None:
            self.name = "TestArtifact"
            self.category = "Test"
            self.web_icon = WebIcon.TEST

        @Search()
        @Search("**/test.sqlite")
        @Search("**/test1.sqlite")
        @Search("**/test2.sqlite")
        def process(self):
            pass

>>>>>>> 7fd0a34a3730e89e70d2f1b8e3580e7acbf60c87
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
