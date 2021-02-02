import html_report.web_icons as web_icons
import jinja2
import globals as g
Icon = web_icons._Icon

jinja = jinja2.Environment(
        loader=jinja2.PackageLoader('ileapp.html_report', 'templates'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        extensions=[IncludeRawExtension],
        trim_blocks=True,
        lstrip_blocks=True,
)

index_html = generate_index(props)
index_file = g.run_time_info['report_folder_base'] / 'index.html'
index_file.write_text(index_html)