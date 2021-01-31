from ileapp.helpers import tsv
from ileapp.helpers.decorators import template
import logging

logger = logging.getLogger(__name__)


class ArtifactHtmlReport:

    def __init__(self, artifact):
        self.name = artifact.name
        self.category = artifact.category
        self.description = artifact.description
        self.headers = artifact.report_headers
        self.props = artifact.props
        self._data = []

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    @template
    def generate_report(self, files_found, template=None, jinja=None):
        template = jinja.get_template('report_base.jinja', None)
        return template.render(
            data=self.data,
            entries=len(self.data),
            headers=self.headers,
            name=self.title,
            location=files_found,
            description=self.description,
            navigation=''
        )

    def report(self, files_found):

        html = self.generate_report(files_found)
        output_file = (self.props.run_time_info['report_folder_base']
                       / f'{self.category} - {self.title}.html')
        with open(output_file, 'w') as report_file:
            report_file.write(html)

        tsv(self.props.run_time_info['report_folder_base'],
            self.headers, self.data, self.name)

        logger.info(f'Report generated for {self.category}[{self.name}]')
