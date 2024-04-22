import importlib
import importlib.util
import inspect
import json
import pathlib
from typing import Generator, cast

from utils import ROOT_TEST_DIR

from xleapp.helpers.filetypes.base import MagicType


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
                    if cls == MagicType:
                        continue
                    yield cast(type[MagicType], cls)


class Config(dict):
    mime_type: str
    extension: str
    example: str = ""

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Config):
            return False
        return (self.mime_type, self.extension) == (__o.mime_type, self.extension)


def get_config(configs: list[Config], mime_type: str, extension: str) -> Config | None:
    for config in configs:
        if mime_type == config["mime_type"] and extension == config["extension"]:
            return config


def create_config(
    configs: dict[str, list[Config]], magic_type: type
) -> tuple[str | None, Config | None, bool]:
    first_cls: type = magic_type.mro()[0]
    parent_module_name: str = first_cls.__module__.split(".")[-1].lower()

    if all(not hasattr(first_cls, attr) for attr in ["MIME", "EXTENSION"]):
        # Anything with these attributes would be a base class
        return None, None, False

    if parent_module_name not in file_types_json_obj:
        file_types_json_obj[parent_module_name] = []

    config: Config | None = get_config(
        configs.get(parent_module_name, []),
        first_cls.MIME,
        first_cls.EXTENSION,
    )

    example_file = get_example_file(first_cls.EXTENSION) or ""

    if config and (not config.get("example") or config.get("example") == example_file):
        config["example"] = example_file
        return parent_module_name, config, True

    if not config:
        return (
            parent_module_name,
            Config(
                mime_type=first_cls.MIME,
                extension=first_cls.EXTENSION,
                example=example_file,
            ),
            False,
        )
    return None, None, False


def get_example_file(extension: str) -> str | None:
    example_files_dir: pathlib.Path = ROOT_TEST_DIR / "data_filetypes"
    file: pathlib.Path

    for file in example_files_dir.glob(f"*.{extension}"):
        return file.name


if __name__ == "__main__":
    file_types_json_obj: dict[str, list[Config]] = {}
    file_types_json: pathlib.Path = (
        pathlib.Path(ROOT_TEST_DIR) / "data_filetypes" / "file_types_lookup.json"
    )

    for magic_type in get_modules_in_packages("xleapp.helpers.filetypes"):
        parent_module, config, update = create_config(file_types_json_obj, magic_type)

        if parent_module and config:
            if update:
                parent = file_types_json_obj[parent_module]
                for num, current_config in enumerate(parent):
                    if current_config == config:
                        del parent[num]
                        parent.append(config)

            else:
                file_types_json_obj[parent_module].append(config)

    with file_types_json.open("w") as file:
        json.dump(file_types_json_obj, file, indent=2)
