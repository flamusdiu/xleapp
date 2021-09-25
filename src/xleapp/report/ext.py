import jinja2
from jinja2.ext import Extension


class IncludeLogFileExtension(Extension):
    tags = {"include_logfile"}

    def parse(self, parser):
        lineno = parser.stream.expect("name:include_logfile").lineno
        filename = parser.parse_expression()
        result = self.call_method("_render", [filename], lineno=lineno)
        return jinja2.nodes.Output([result], lineno=lineno)

    def _render(self, filename):
        file_text = "".join(
            (self.environment.loader.get_source(self.environment, filename)[0]).split(
                "\r"
            )
        )
        return jinja2.Markup(f'<pre class="log-file">{file_text}</pre>')
