import json
import pathlib

from utils import ROOT_TEST_DIR, get_modules_in_packages


class Config(dict):
    mime_type: str
    extension: str
    examples: list[str] = []

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

    example_files: list[str] = get_example_files(first_cls.EXTENSION) or []
    example_files.sort()

    if config:
        current_example_files: list[str] | None = config.get("examples")
        if not current_example_files or current_example_files == example_files:
            config["examples"] = example_files
            return parent_module_name, config, True

    if not config:
        return (
            parent_module_name,
            Config(
                mime_type=first_cls.MIME,
                extension=first_cls.EXTENSION,
                examples=example_files,
            ),
            False,
        )
    return None, None, False


def get_example_files(extension: str) -> list[str] | None:
    example_files_dir: pathlib.Path = ROOT_TEST_DIR / "data_filetypes"
    files: list[str] = [file.name for file in example_files_dir.glob(f"*.{extension}")]
    return files


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
