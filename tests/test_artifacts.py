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
                    row_dict = dict_from_row(row)  # noqa
                    self.data.append(tuple(row_dict.values()))


@pytest.fixture
def artifact(mocker, test_search_providers):

    mocker.patch("xleapp.report.db.KmlDBManager._create", return_value=None)
    mocker.patch("xleapp.report.db.TimelineDBManager._create", return_value=None)
    mocker.patch("xleapp.app.search_providers", test_search_providers)
    return TestArtifact()


class TestArtifactCreation:
    def test_create(self, artifact):
        assert isinstance(artifact, Artifact)

    def test_attach_app(self, artifact, app):
        artifact.app = app
        assert isinstance(artifact.app, Application)


class TestArtifactContactManager:
    @pytest.fixture
    def artifact_context(self, artifact, app):
        artifact.app = app
        artifact.regex = (
            ("**/files"),
            ("**/files2", "return_on_first_hit", "file_names_only"),
        )

        with artifact.context() as af:
            yield af

    def test_contact_manager(self, artifact_context):
        assert isinstance(artifact_context, Artifact)
