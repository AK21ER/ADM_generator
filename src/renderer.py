from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

def render_report(template_root: Path, output_path: Path, client, financial, sections, matrix, roadmap, benchmarks, financial_chart_svg):
    env = Environment(loader=FileSystemLoader(str(template_root)), autoescape=select_autoescape(["html", "xml"]))
    tpl = env.get_template("base.html.j2")
    html = tpl.render(client=client, financial=financial, sections=sections, matrix=matrix, roadmap=roadmap, benchmarks=benchmarks, financial_chart_svg=financial_chart_svg)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return html
