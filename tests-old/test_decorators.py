import pytest

from xleapp.artifact.abstract import Artifact
from xleapp.artifact.decorators import core_artifact, long_running_process


class DummyArtifactClass(Artifact, category="Dummy", label="Dummy Artifact"):
    pass

    def process(self):
        pass


class DummyClass:
    pass


@pytest.mark.parametrize(
    "decorator, attribute_name",
    [(core_artifact, "core"), (long_running_process, "long_running_process")],
)
def test_decorate_set_attribute(decorator, attribute_name):
    test_artifact = decorator(DummyArtifactClass)
    test_artifact_obj = test_artifact()

    assert getattr(test_artifact_obj, attribute_name)


@pytest.mark.parametrize(
    "decorator, attribute_name",
    [(core_artifact, "core"), (long_running_process, "long_running_process")],
)
def test_decorate_set_attribute_wrong_class(decorator, attribute_name):
    with pytest.raises(AttributeError):
        decorator(DummyClass)
