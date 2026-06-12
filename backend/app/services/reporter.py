from jinja2 import Environment, FileSystemLoader
import os
from app.models.finding import Finding
from app.models.target import Target

def generate_html_report(finding: Finding, target: Target) -> str:
    """
    Renders the Jinja2 template into an HTML string.
    """
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')))
    template = env.get_template('report_template.html')
    
    html_out = template.render(finding=finding, target=target)
    return html_out

def html_to_pdf(html_content: str, output_path: str):
    """
    Mocks HTML to PDF conversion using Puppeteer.
    In reality, we would use pyppeteer or a similar library here.
    """
    # For the architecture implementation plan, we write the HTML instead
    with open(output_path.replace(".pdf", ".html"), "w") as f:
        f.write(html_content)
    
    # Return path to simulated PDF
    return output_path
