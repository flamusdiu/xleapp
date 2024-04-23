import bisect
import json
import pathlib
from pytest import Metafunc
import pytest

from tests.utils.utils import ROOT_TEST_DIR, get_modules_in_packages
from xleapp.helpers.filetypes.base import MagicType
from xleapp.helpers.filetype import guess


def create_filetype_scenarios() -> dict[str, dict]:
    path = pathlib.Path(ROOT_TEST_DIR) / "data_filetypes" / "file_types_lookup.json"

    with path.open() as file:
        configs: dict[str, list[dict]] = json.load(file)

    scenarios: dict[str, dict] = {}

    for category, config in configs.items():
        for mime_config in config:
            scenario_name = f"{category}_{mime_config['mime_type']}"
            scenarios[scenario_name] = mime_config

    return scenarios


def pytest_generate_tests(metafunc: Metafunc):
    idlist, argnames, argvalues = [], [], []

    def generate_ids() -> list[str]:
        idlist: list[str] = []
        for scenerio in metafunc.cls.scenarios.keys():
            bisect.insort(idlist, scenerio)

        return idlist

    def generate_scenarios_based_on_attr(*attr: str) -> tuple[list[str], list, list]:
        argvalues: list = []
        scenario: str

        idlist = generate_ids()

        for scenario in idlist:
            items = metafunc.cls.scenarios[scenario].items()
            argnames = [x[0] for x in items if x[0] in attr]
            argvalues.append([x[1] for x in items if x[0] in attr])
        return idlist, argnames, argvalues

    attrs = []
    if "mime_type" in metafunc.fixturenames:
        attrs.append("mime_type")

    if "extension" in metafunc.fixturenames:
        attrs.append("extension")

    if "examples" in metafunc.fixturenames:
        attrs.append("examples")

    idlist, argnames, argvalues = generate_scenarios_based_on_attr(*attrs)
    if idlist and argnames and argvalues:
        metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


@pytest.fixture(scope="module")
def magic_types() -> list[type[MagicType]]:
    return list(get_modules_in_packages("xleapp.helpers.filetypes"))


class TestFileTypesWithScenarios:
    scenarios: dict[str, dict] = create_filetype_scenarios()
    test_files_dir: pathlib.Path = ROOT_TEST_DIR / "data_filetypes"

    def test_mime_type(self, mime_type: str) -> None:
        assert isinstance(mime_type, str)
        assert mime_type is not None

    def test_extension(self, extension: str) -> None:
        assert isinstance(extension, str)
        assert extension is not None

    def test_example(self, examples: list[str]) -> None:
        assert isinstance(examples, list)
        assert all(isinstance(item, str) for item in examples)

    def test_file_file_matcher(
        self, mime_type: str, examples: str, magic_types: list[type[MagicType]]
    ) -> None:
        if not examples:
            pytest.skip("No example file for test.")

        for example in examples:
            test_file = self.test_files_dir / example

            if not test_file.exists():
                raise FileExistsError(
                    f"File {{{test_file}}} does not exists for type {{{mime_type}}} but is configured!"
                )

            cls: list[type[MagicType]] = [c for c in magic_types if c.MIME == mime_type]
            if not cls:
                raise Exception(f"No class definition found for mime {{{mime_type}}}!")

            if len(cls) > 1:
                raise Exception(
                    f"More then on class definition found for mime {{{mime_type}}}!"
                )

            single_cls: MagicType = cls.pop()()

            with test_file.open("rb") as file:
                test_guess: MagicType | None = guess(file)
                assert (
                    test_guess == single_cls
                ), f"File {{{test_file}}} does not match type {{{mime_type}}}!"
