import functools
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path

import jinja2

import xleapp.globals as g
import xleapp.report.webicons as webicons
from xleapp import VERSION
from xleapp._authors import __authors__, __contributors__
from xleapp.report.ext import IncludeLogFileExtension

jinja = jinja2.Environment


def init_jinja(log_folder):
    """Sets up Jinja2 templating for HTML report

    Args:
        log_folder (Path): Log folder for the log output]
    """

    global jinja
    template_loader = jinja2.PackageLoader("xleapp.report", "templates")
    log_file_loader = jinja2.FileSystemLoader(log_folder)

    jinja = jinja2.Environment(
        loader=jinja2.ChoiceLoader([template_loader, log_file_loader]),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
        extensions=[jinja2.ext.do, IncludeLogFileExtension],
        trim_blocks=True,
        lstrip_blocks=True,
    )


class Template:
    """Template decorator for HTML pages

    This is used to decorate a custom class's HTML function to change
    the Jinja2 template being used.

    Example:

        Create a new class extending from HtmlPage base class. Then,
        create a `html()` function which is decorated by this function
        which provides the template name. This function will attached
        the `template` attribute automatically which is used to return the
        HTML of the template page.

        This replaces the default report page with this template.

        class MyCustomPage(HtmlPage):
            @Template('mytemplate')
            def html(self) -> str:
                return self.template.render(renderingVals)

     Args:
         template(str): Name of Jinja template without extension.
             Must be in template folder.
    """

    def __init__(self, template: str):
        self._template = f"{template}.jinja"

    def __call__(self, func):
        @functools.wraps(func)
        def template_wrapper(cls, *args):
            template_j = jinja.get_template(self._template, None)
            cls.template = template_j
            return func(cls)

        return template_wrapper


@dataclass
class Contributor:
    """Contributor's information displayed on main index page.

    Attributes:
        name (str): Name of Contributor
        website(str): Website of Contributor
        twitter (str): Twitter handle of the Contributor
        github (str): Github url for Contributor
    """

    name: str
    website: str = ""
    twitter: str = ""
    github: str = ""


@dataclass
class NavigationItem:
    """Navigation item for HTML report

    Attributes:
        name (str): Artifact Name
        href (str): URL of Artifact's report
        web_icon (webicons.Icon): Feather ICON for Artifact in
            the navigation list
    """

    name: str
    href: str
    web_icon: webicons.Icon

    def __str__(self) -> str:
        return f'<a class="nav-link" href="{self.href}"><span data-feather="{self.web_icon}"></span>{self.name}</a>'

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        return self.name == other.name


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


def generate_nav(report_folder: PathLike, selected_artifacts: list) -> dict:
    """Generates a dictionary containing the navigation of the
       report.

    Args:
        report_folder (PathLike): Report folder where Artifact HTML Reports
            are saved.
        selected_artifacts (list): List of selected
            Artifacts for the report

    Returns:
        dict: dictionary of navigation items for HTML Report
    """
    nav = defaultdict(set)

    for _, artifact in selected_artifacts:
        if not artifact.core:
            temp_item = NavigationItem(
                name=artifact.name,
                web_icon=artifact.web_icon.value,
                href=(report_folder / f"{artifact.category} - {artifact.name}.html"),
            )
            nav[artifact.category].add(temp_item)
    return nav


@dataclass
class _HtmlPageDefaults:
    """HTML page defaults for the HTML page

    Attributes:
        report_folder (Path): Report folder where Artifact HTML Reports
            are saved.
        log_folder (Path): Log folder for the log output
        extraction_type (str): Type of the extraction
        processing_time (float): Float number for time it took to run
            application
        device (Device): Extracted device information object
        project (str): project name
        version (str): project version
        navigation (dict): Navigation of the HTML report
    """

    report_folder: Path = field(default="", init=True)
    log_folder: Path = field(default="", init=True)
    extraction_type: str = field(default="fs", init=True)
    processing_time: float = field(default=0.0, init=True)
    project: str = field(default=VERSION.split(" ")[0], init=False)
    version: str = field(default=VERSION.split(" ")[1], init=False)
    navigation: dict = field(default_factory=lambda: {}, init=False)


@dataclass
class HtmlPage(ABC, _HtmlPageDefaults):
    device: object = field(init=False)

    def __post_init__(self):
        self.device = g.device

    @abstractmethod
    def html(self):
        raise NotImplementedError('HtmlPage objects must implement "html()" method!')


@dataclass
class Index(HtmlPage):
    """Main index page for HTML report

    Attributes:
        authors (list): list of authors
        contributors (list): list of contributors
    """

    authors: list = field(
        init=False,
        default_factory=lambda: get_contributors(__authors__),
    )
    contributors: list = field(
        init=False,
        default_factory=lambda: get_contributors(__contributors__),
    )

    @Template("index")
    def html(self) -> str:
        """Generates html for page

        Note:
            A 'empty' artifact object is used here to generate the report.
            Every HTML page is attached to an artifact but this one which is
            the reason the usage of the 'fake' artifact.

        Returns:
            str: HTML of the page
        """
        from xleapp.abstract import AbstractArtifact

        class Artifact(AbstractArtifact):
            def process(self):
                pass

        artifact = Artifact()
        artifact.html_report = self
        log_file = str((self.log_folder / "xleapp.log").absolute())

        return self.template.render(
            artifact=artifact,
            log_file=log_file,
            navigation=self.navigation,
        )
