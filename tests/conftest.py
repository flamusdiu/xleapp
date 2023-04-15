import contextlib
import pathlib
import shutil

from dataclasses import dataclass

import pytest
import requests
import xleapp
import xleapp.globals

from tqdm import tqdm
from xleapp import Artifact, Search, WebIcon
from xleapp.app import Application, Device


ios_13_4_1_zip = (
    "https://digitalcorpora.s3.amazonaws.com/corpora/mobile/ios_13_4_1/ios_13_4_1.zip"
)

optional_markers = {
    "download": {
        "help": "downloads archives for tests. Greatly slows down tests!",
        "marker-descr": "downloads archives for testing. Tests will take longer!",
        "skip-reason": "Test only runs with the --{} option.",
    },
}


def pytest_addoption(parser):
    for marker, info in optional_markers.items():
        parser.addoption(
            "--{}".format(marker),
            action="store_true",
            default=False,
            help=info["help"],
        )


def pytest_configure(config):
    for marker, info in optional_markers.items():
        config.addinivalue_line("markers", "{}: {}".format(marker, info["marker-descr"]))


def pytest_collection_modifyitems(config, items):
    for marker, info in optional_markers.items():
        if not config.getoption("--{}".format(marker)):
            skip_test = pytest.mark.skip(reason=info["skip-reason"].format(marker))
            for item in items:
                if marker in item.keywords:
                    item.add_marker(skip_test)


@pytest.fixture(scope="session", autouse=True)
def test_data(request):
    return request.config.cache.makedir("test-data")


@pytest.mark.download
@pytest.fixture(scope="session", autouse=True)
def ios_image(test_data, request, pytestconfig):
    """Downloads and saves ios Image. Most test will use this file system image.
    This is extracted a head of time due to the overhead of trying to extract
    during testing.
    """

    # seems autouse always happens even if set to skip. This forces the skip.
    if not pytestconfig.getoption("--download"):
        return pathlib.Path.cwd()

    fn = pathlib.Path(test_data / "ios_13_4_1.zip")
    ios_file_extraction_root = test_data / "iOS 13.4.1 Extraction/Extraction"
    ios_file_sys = test_data / "13-4-1"

    request.config.cache.set("xleapp/ios-image-13-4-1", str(ios_file_sys))

    fn.touch(exist_ok=True)

    if fn.stat().st_size == 0:
        req = requests.get(ios_13_4_1_zip, stream=True)
        total_size = int(req.headers.get("content-length"))
        initial_pos = 0

        with fn.open(mode="b+a") as f:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=fn.name,
                initial=initial_pos,
                ascii=True,
            ) as progress_bar:
                for ch in req.iter_content(chunk_size=1024):
                    if ch:
                        f.write(ch)
                        progress_bar.update(len(ch))

    if not ios_file_extraction_root.exists():
        shutil.unpack_archive(str(fn), extract_dir=str(test_data))

    if not ios_file_sys.exists():
        # some files just do not extract
        with contextlib.suppress(FileNotFoundError):
            shutil.unpack_archive(
                str(ios_file_extraction_root / "13-4-1.tar"),
                extract_dir=str(ios_file_sys),
            )

    # Return the file system directory after the second extraction
    return ios_file_sys


@pytest.fixture
def test_artifact():
    class TestArtifact(Artifact, category="Test", label="Test Artifact"):
        __test__ = False
        device_type = "test"

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

    return dataclass(TestArtifact, frozen=True, eq=True)


@pytest.fixture
def fake_filesystem(fs, test_data):
    """Variable name 'fs' causes a pylint warning. Provide a longer name
    acceptable to pylint for use in tests.
    """
    fs.add_real_directory(test_data)
    yield fs


@pytest.fixture
def app(
    fake_filesystem,
    mocker,
    monkeypatch,
    fake_kml_db_manager,
    fake_timeline_db_manager,
    fake_search_providers,
    test_artifact,
):
    def fake_discover_plugins():
        test_artifact()

    fake_filesystem.makedir("reports")
    output_path = pathlib.Path() / "reports"

    mocker.patch(
        "xleapp.app.Application.discover_plugins", return_value=fake_discover_plugins()
    )
    app = Application()
    for artifact in app.artifacts:
        artifact.select = True

    try:
        monkeypatch.setattr(xleapp.globals, "app", app)
    except AttributeError:
        xleapp.globals.app = app

    app.device.update({"Type": "device_type"})
    app.output_path = output_path

    yield app()

    shutil.rmtree(app.report_folder)


@pytest.fixture
def test_device():
    return Device(
        {
            "IOS Version": 14.6,
            "ProductBuildVersion": "18F72",
            "Product": "iPhone OS",
            "Last Known ICCID": "89012803320056608813",
            "Reported Phone Number": "19048075555",
            "IMEI": "356720085253071",
        }
    )


@pytest.fixture
def fake_kml_db_manager(mocker):
    mocker.patch("xleapp.report.db.KmlDBManager.create", return_value=None)


@pytest.fixture
def fake_timeline_db_manager(mocker):
    mocker.patch("xleapp.report.db.TimelineDBManager.create", return_value=None)


@pytest.fixture
def fake_search_providers(mocker):
    class provider:
        validate = True
        priority = 10
        file_handles = object()

        def search(self, regex):
            return iter([])

    class SearchProvider:
        data = {"FS": provider()}

        def __call__(self, extraction_type, *, input_path, **kwargs):
            return self.data["FS"]

    mocker.patch("xleapp.app.search_providers", SearchProvider())


def test_app_input_path(ios_image, app):
    assert app.input_path == ios_image


def test_app_output_path(app, tmp_path_factory):
    assert app.output_path == tmp_path_factory / "data"
