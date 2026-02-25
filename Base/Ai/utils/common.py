from jinja2 import Template

def jinja2_prompt_render(prompt, params):
    template = Template(prompt)
    return template.render(params)