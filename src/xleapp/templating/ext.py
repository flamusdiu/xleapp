from __future__ import annotations

import typing as t

import jinja2
import jinja2.ext

from jinja2 import nodes
from jinja2.utils import markupsafe


if t.TYPE_CHECKING:
    from jinja2.parser import Parser


class IncludeLogFileExtension(jinja2.ext.Extension):
    tags = {"include_logfile"}

    def parse(self, parser: Parser) -> t.Union[nodes.Node, t.List[nodes.Node]]:
        lineno = parser.stream.expect("name:include_logfile").lineno
        filename = parser.parse_expression()
        result = self.call_method("_render", [filename], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, template: str) -> t.Any:
        try:
            source, _, _ = self.environment.loader.get_source(self.environment, template)
            file_text = "".join(source.split("\r"))
        except Exception:
            file_text = f"{template} not found or missing! No logs available."
        return markupsafe.Markup(f'<pre class="log-file">{file_text}</pre>')
