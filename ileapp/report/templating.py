import functools
from abc import ABC, abstractmethod
from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from pathlib import Path

import ileapp.globals as g
import jinja2
from ileapp import VERSION, __authors__, __contributors__
from ileapp.report.ext import IncludeLogFileExtension

jinja = jinja2.Environment


def init_jinja(log_folder):

    global jinja
    template_loader = jinja2.PackageLoader('ileapp.report', 'templates')
    log_file_loader = jinja2.FileSystemLoader(log_folder)

    jinja = jinja2.Environment(
        loader=jinja2.ChoiceLoader([template_loader, log_file_loader]),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        extensions=[jinja2.ext.do,
                    IncludeLogFileExtension],
        trim_blocks=True,
        lstrip_blocks=True,
    )


class Template:
    def __init__(self, template: str):
        self._template = f'{template}.jinja'

    def __call__(self, func):
        @functools.wraps(func)
        def template_wrapper(cls, *args):
            template_j = jinja.get_template(self._template, None)
            setattr(cls, 'template', template_j)
            return func(cls)
        return template_wrapper


def get_contributors(contributors):
    contrib_list = []

    Contributor = namedtuple('Contributor',
                             ['name', 'website', 'twitter', 'github'])

    for row in contributors:
        contrib_list.append(
            Contributor(
                name=row[0],
                website=row[1] or '',
                twitter=row[2] or '',
                github=row[3] or ''
            )
        )
    return contrib_list


def generate_nav(report_folder, selected_artifacts):
    nav = defaultdict(set)
    Item = namedtuple('Item', ['name', 'href', 'web_icon'])

    for artifact in selected_artifacts:
        temp_item = Item(
            name=artifact.name,
            web_icon=artifact.web_icon.value,
            href=(report_folder
                  / f'{artifact.category} - {artifact.name}.html'))
        nav.update({artifact.category: temp_item})
    return dict(nav)


@dataclass
class _HtmlPageDefaults:
    report_folder: Path = field(default='', init=True)
    log_folder: Path = field(default='', init=True)
    extraction_type: str = field(default='fs', init=True)
    processing_time: float = field(default=0.0, init=True)
    device: g.Device = field(default=g.device, init=False)
    project: str = field(default=VERSION.split(' ')[0], init=False)
    version: str = field(default=VERSION.split(' ')[1], init=False)
    # navigation: dict = field(default_factory=lambda: {}, init=False)


@dataclass
class HtmlPage(ABC, _HtmlPageDefaults):

    @abstractmethod
    def html(self):
        raise NotImplementedError(
            'HtmlPage objects must implement \'html()\' method!')


@dataclass
class Index(HtmlPage):
    authors: list = field(
        init=False, default_factory=lambda: get_contributors(__authors__))
    contributors: list = field(
        init=False, default_factory=lambda: get_contributors(__contributors__))

    @Template('index')
    def html(self):
        from ileapp.abstract import AbstractArtifact

        class Artifact(AbstractArtifact):
            def process(self):
                pass

        artifact = Artifact()
        artifact.html_report = self
        log_file = str((self.log_folder / 'ileapp.log').absolute())

        return self.template.render(artifact=artifact, log_file=log_file)
