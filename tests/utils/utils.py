import importlib
import importlib.util
import inspect
import pathlib
from typing import Generator, cast

from xleapp.helpers.filetypes.base import MagicType

ROOT_TEST_DIR = pathlib.Path(__file__).parent.parent
ROOT_PROJECT = ROOT_TEST_DIR.parent
ROOT_APPLICATION = ROOT_PROJECT / "src" / "xleapp"


class PackageNotFound(Exception):
    """Package not found or invalid"""


def get_modules_in_packages(package_name: str) -> Generator[type[MagicType], None, None]:
    package = importlib.util.find_spec(package_name)

    if not package or not package.origin:
        raise PackageNotFound(f"Package {{{package_name}}} not found or invalid!")

    files: Generator[pathlib.Path, None, None] = pathlib.Path(
        package.origin
    ).parent.iterdir()
    file: pathlib.Path

    for file in files:
        if file not in ["__init__.py", "__pycache__.py"]:
            if file.suffix != ".py":
                continue

            package = f"{package_name}.{file.stem}"
            for _name, cls in inspect.getmembers(
                importlib.import_module(package), inspect.isclass
            ):
                if MagicType in cls.mro():
                    if (
                        cls == MagicType
                        or not hasattr(cls, "MIME")
                        or not hasattr(cls, "EXTENSION")
                    ):
                        continue
                    yield cast(type[MagicType], cls)
