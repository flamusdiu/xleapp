import pytest

from xleapp import Artifact
from xleapp.app import Application


class TestArtifactCreation:
    def test_create(self, artifact):
        assert isinstance(artifact, Artifact)

    def test_attach_app(self, artifact, app):
        assert isinstance(artifact.app, Application)


class TestArtifactContextManager:
    @pytest.fixture
    def artifact_context(self, artifact, app):
        artifact.app = app
        artifact.regex = (
            ("**/files"),
            ("**/files2", "return_on_first_hit", "file_names_only"),
        )

        with artifact.context() as af:
            yield af

    def test_contact_manager_creation(self, artifact_context):
        assert isinstance(artifact_context, Artifact)
