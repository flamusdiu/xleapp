import typing
from dataclasses import dataclass, field
from os import PathLike

import xleapp.report.kml as kml
import xleapp.report.timeline as timeline
import xleapp.report.tsv as tsv
from xleapp.report.templating import HtmlPage, Template

if typing.TYPE_CHECKING:
    from xleapp.artifacts.abstract import AbstractArtifact


@dataclass
class ArtifactHtmlReport(HtmlPage):

    artifact: "AbstractArtifact" = field(init=False, default=None)
    artifact_cls: str = field(init=False, default='Artifact')
    data: list = field(init=False, default_factory=lambda: [])
    report_folder: PathLike = field(init=False, default=None)

    @Template("report_base")
    def html(self):
        return self.template.render(artifact=self.artifact, navigation=self.navigation)

    def report(self):
        html = self.html()
        output_file = (
            self.report_folder / f"{self.artifact.category} - {self.artifact.name}.html"
        )
        output_file.write_text(html)

        if self.artifact.processed:
            tsv.save(
                self.report_folder,
                self.artifact.report_headers,
                self.artifact.data,
                self.artifact.name,
            )

            if self.artifact.kml:
                kml.save(
                    self.artifact.name, self.artifact.data, self.artifact.report_headers
                )

            if self.artifact.timeline:
                timeline.save(
                    self.artifact.name, self.artifact.data, self.artifact.report_headers
                )

    def set_artifact(self, artifact: "AbstractArtifact"):
        self.artifact_cls = type(artifact).__name__
        self.artifact = artifact
