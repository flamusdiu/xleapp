from functools import cache, cached_property
import typing as t
from collections import defaultdict
from os import PathLike
from pathlib import Path

from xleapp.artifacts.services import ArtifactService

from ._ext import IncludeLogFileExtension
from ._html import ArtifactHtmlReport, Contributor, HtmlPage, NavigationItem, Template
from ._partials.index import Index

if t.TYPE_CHECKING:
    from xleapp.app import XLEAPP


def generate_index(app: "XLEAPP") -> None:

    nav = generate_nav(app.report_folder, app.artifacts)

    index_page = Index(
        app.report_folder, app.log_folder, app.extraction_type, app.processing_time, nav
    )
    index_file = app.report_folder / "index.html"
    index_file.write_text(index_page.html())


def get_contributors(contributors: list) -> list[Contributor]:
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


def generate_nav(report_folder: PathLike, artifacts: ArtifactService) -> dict:
    """Generates a dictionary containing the navigation of the
       report.

    Args:
        report_folder (PathLike): Report folder where Artifact HTML Reports
            are saved.
        artifacts (ArtifactService): service containing all artifacts
            Artifacts for the report

    Returns:
        dict: dictionary of navigation items for HTML Report
    """
    nav = defaultdict(set)

    for artifact in artifacts.values():
        if not artifact.core and artifact.selected:
            temp_item = NavigationItem(
                name=artifact.name,
                web_icon=artifact.web_icon.value,
                href=(report_folder / f"{artifact.category} - {artifact.name}.html"),
            )
            nav[artifact.category].add(temp_item)
    return nav
