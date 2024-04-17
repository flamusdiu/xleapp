import pytest

from xleapp import Artifact


class TestArtifactCreation:
    def test_create(self, test_artifact):
        assert isinstance(test_artifact(), Artifact)


class TestArtifactContextManager:
    @pytest.fixture
    def artifact_context(self, test_artifact):
        test_af: Artifact = test_artifact()
        test_af.regex = "**/files"
        test_af.regex = ("**/files2", False, True)

        with test_af.context() as af:
            yield af

    def test_contact_manager_creation(self, artifact_context):
        assert isinstance(artifact_context, Artifact)
