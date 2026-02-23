from jinja2 import Template


def prompt_render(prompt, params):
    template = Template(prompt)
    return template.render(params)