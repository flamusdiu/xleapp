import typing as t

from collections import defaultdict
from pathlib import Path

from ._partials.index import Index
from .ext import IncludeLogFileExtension as IncludeLogFileExtension
from .html import ArtifactHtmlReport as ArtifactHtmlReport
from .html import Contributor
from .html import HtmlPage as HtmlPage
from .html import NavigationItem
from .html import Template as Template


if t.TYPE_CHECKING:
    from xleapp.app import Application
    from xleapp.artifacts.services import Artifacts


def generate_index(app: "Application") -> None:

    nav = generate_nav(app.report_folder, app.artifacts)

    index_page = Index(
        report_folder=app.report_folder,
        log_folder=app.log_folder,
        extraction_type=app.extraction_type,
        processing_time=app.processing_time,
        navigation=nav,
    )  # type: ignore

    index_file = app.report_folder / "index.html"
    index_file.write_text(index_page.html())


def get_contributors(contributors: list[list[str]]) -> list[Contributor]:
    """Returns a list of Contributors from `xleapp.__contributors__`

    Args:
        contributors (list): List of contributors

    Returns:
        List(Contributor): List of contributors objects for HTML Report
    """
    contrib_list = []

    for row in contributors:
        contrib_list.append(Contributor(*row))
    return contrib_list


def generate_nav(
    report_folder: Path,
    artifacts: "Artifacts",
) -> dict[str, set[NavigationItem]]:
    """Generates a dictionary containing the navigation of the
       report.

    Args:
        report_folder (Path): Report folder where Artifact HTML Reports
            are saved.
        artifacts (ArtifactService): service containing all artifacts
            Artifacts for the report

    Returns:
        dict: dictionary of navigation items for HTML Report
    """
    nav = defaultdict(set)

    for artifact in artifacts.data:
        if not artifact.core and artifact.select:
            temp_item = NavigationItem(
                name=artifact.value.name,
                web_icon=artifact.web_icon.value,
                href=str(
                    report_folder / f"{artifact.category} - {artifact.value.name}.html"
                ),
            )
            nav[artifact.category].add(temp_item)
    return nav
