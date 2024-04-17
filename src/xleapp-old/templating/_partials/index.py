from dataclasses import dataclass, field

from xleapp import templating
from xleapp._authors import __authors__, __contributors__
from xleapp.templating import html


@dataclass
class Index(html.HtmlPage):
    """Main index page for HTML report

    Attributes:
        authors (list): list of authors
        contributors (list): list of contributors
    """

    authors: list[html.Contributor] = field(init=False)
    contributors: list[html.Contributor] = field(init=False)

    def __post_init__(self) -> None:
        self.authors = templating.get_contributors(__authors__)
        self.contributors = templating.get_contributors(__contributors__)

    @html.Template("index")
    def html(self) -> str:
        """Generates html for page

        Returns:
            str: HTML of the index page
        """

        return self.template.render(
            navigation=self.navigation,
            authors=self.authors,
            contributors=self.contributors,
        )
