import importlib
import shutil
from collections import defaultdict, namedtuple
from pathlib import Path
from ileapp.helpers.decorators import template
import ileapp.html_report as report
import ileapp.html_report.web_icons as web_icons
import jinja2
from ileapp import __authors__, __contributors__
from ileapp.html_report.templating import IncludeRawExtension

Icon = web_icons._Icon


def init(props):
    """Initialize the reports module

    Args:
        props (Props): global property module
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('ileapp.html_report', 'templates'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        extensions=[IncludeRawExtension],
        trim_blocks=True,
        lstrip_blocks=True,
    )
    props.jinja = env
    props.html_report = report

    copy_static_files(props.run_time_info['report_folder_base'])

    index_html = generate_index(props)
    index_file = props.run_time_info['report_folder_base'] / 'index.html'
    index_file.write_text(index_html)

@template('index.jinja')
def generate_index(props):
    project, version = props.version.split(' ')
    authors, contributors = get_contributors(__authors__, __contributors__)

    return template.render(
        navigation='',
        authors=authors,
        contributors=contributors,
        processing_time=props.run_time_info['processing_time'],
        report_directory=props.run_time_info['report_folder_base'],
        extraction_type=props.run_time_info['extraction_type'],
        device=props.device_info,
        version=f'{project} {version}')


def generate_nav(props, report_folder, artifacts):
    nav = defaultdict(set)
    Item = namedtuple('Item', ['name', 'href', 'web_icon'])
    for name in artifacts:
        artifact = props.installed_artifacts[name]
        temp_item = Item(
            name=artifact.cls.name,
            web_icon=artifact.cls.web_icon.value,
            href=str(report_folder / f'{artifact.cls.category} - {artifact.cls.name}.html')
        )
        nav.update({artifact.cls.category: temp_item})
    return dict(nav)


def get_contributors(authors, contributors):
    """Translates the list of contributors a dictionary

    Args:
        authors (list): list of authors
        contributors (list): list of contributors

    Returns:
        dict: translated list of contributors
    """
    contrib_list = []
    author_list = []

    Contributor = namedtuple('Contributor', ['name', 'website', 'twitter', 'github'])

    for row in authors:
        author_list.append(
            Contributor(
                name=row[0],
                website=row[1] or '',
                twitter=row[2] or '',
                github=row[3] or ''
            )
        )

    for row in contributors:
        contrib_list.append(
            Contributor(
                name=row[0],
                website=row[1] or '',
                twitter=row[2] or '',
                github=row[3] or ''
            )
        )
    return [author_list, contrib_list]


def copy_static_files(report_folder):
    html_report_root = Path(importlib.util.find_spec(__name__).origin).parent
    static_folder = html_report_root / '_static'
    logo = html_report_root.parent.parent / 'logo.jpg'

    report_folder = report_folder / '_static'

    shutil.copytree(static_folder, report_folder)
    shutil.copy(logo, static_folder)
