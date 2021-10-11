from dataclasses import dataclass, field

from xleapp._authors import __authors__, __contributors__

import xleapp.templating as templating
from .._html import HtmlPage, Template


@dataclass
class Index(HtmlPage):
    """Main index page for HTML report

    Attributes:
        authors (list): list of authors
        contributors (list): list of contributors
    """

    authors: list = field(init=False)
    contributors: list = field(init=False)

    def __post_init__(self):
        self.authors = templating.get_contributors(__authors__)
        self.contributors = templating.get_contributors(__contributors__)

    @Template("index")
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
