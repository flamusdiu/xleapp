import pytest
from xleapp import Artifact, Search, WebIcon


@pytest.fixture
def test_artifact():
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

    return Accounts()


@pytest.fixture
def test_artifact_multiple_search():
    class TestArtifact(Artifact):
        def __post_init__(self) -> None:
            self.name = "TestArtifact"
            self.category = "Test"
            self.web_icon = WebIcon.TEST

        @Search("**/test.sqlite")
        @Search("**/test1.sqlite")
        @Search("**/test2.sqlite")
        def process(self):
            pass

    return TestArtifact()


def test_create_artifact(test_artifact):
    assert isinstance(test_artifact, Artifact)


def test_create_artifact_search(test_artifact, app):
    test_artifact.app = app
    test_artifact.process()
    assert len(test_artifact.regex) == 1


def test_create_artifact_multiple_search(test_artifact_multiple_search, app):
    test_artifact_multiple_search.app = app
    test_artifact_multiple_search.process()
    assert len(test_artifact_multiple_search.regex) == 3


def test_create_artifact_missing_process():
    class TestArtifact(Artifact):
        def __post_init__(self) -> None:
            self.name = "TestArtifact"
            self.category = "Test"
            self.web_icon = WebIcon.TEST

    with pytest.raises(TypeError):
        artifact = TestArtifact()