from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

template_engine = Environment(loader=FileSystemLoader("app/templates/"))

def html(response, template_file: str):
    template = template_engine.get_template(template_file)
    html_content = template.render(data=response)
    return HTMLResponse(content=html_content)

def multi_modal(response, template_file: str, request: Request):
    if 'text/html' in request.headers.get('Accept',''):
        return html(response, template_file)
    else:
        return response