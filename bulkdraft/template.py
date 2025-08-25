"""
Template processing and rendering functionality.
"""

import yaml
from jinja2 import Template, Environment, BaseLoader


def load_content(md_file):
    """
    Load template file and extract YAML metadata and markdown content.
    
    Args:
        md_file (str): Path to the template file with YAML front matter
        
    Returns:
        tuple: (metadata dict, markdown content string)
    """
    with open(md_file, 'r') as file:
        content = file.read()
    
    # Split YAML front matter and markdown content
    _, yaml_part, md_part = content.split('---', 2)
    metadata = yaml.safe_load(yaml_part)
    
    return metadata, md_part


def render_template(template_content, metadata, context_data=None):
    """
    Render Jinja2 template with metadata and context data.
    
    Args:
        template_content (str): Template content to render
        metadata (dict): Metadata from YAML front matter
        context_data (dict, optional): Context data from CSV/YAML files
        
    Returns:
        str: Rendered template content
    """
    # Create Jinja2 environment
    env = Environment(loader=BaseLoader())
    template = env.from_string(template_content)
    
    # Build render context starting with empty dict so Jinja2 defaults work
    render_context = {}
    
    # Add metadata values that are already resolved (not template strings)
    if metadata:
        for key, value in metadata.items():
            if isinstance(value, str) and not (value.startswith('{{') and value.endswith('}}')):
                render_context[key] = value
    
    # Add context data from CSV/YAML (highest priority)
    if context_data:
        render_context.update(context_data)
    
    # Render the template
    rendered = template.render(**render_context)
    return rendered


def render_metadata_templates(metadata, record):
    """
    Render YAML metadata templates with context data.
    
    Args:
        metadata (dict): Raw metadata from YAML front matter
        record (dict): Context data for current recipient
        
    Returns:
        dict: Rendered metadata with template variables resolved
    """
    rendered_metadata = {}
    
    # First pass: render basic templates (not subject which may depend on others)
    for key, value in metadata.items():
        if isinstance(value, str) and key != 'subject':
            try:
                rendered_value = render_template(value, {}, record)
                rendered_metadata[key] = rendered_value
                print(f"Debug: {key}: '{value}' -> '{rendered_value}'")
            except Exception as e:
                print(f"Warning: Failed to render {key}: {e}")
                rendered_metadata[key] = value
        elif not isinstance(value, str):
            rendered_metadata[key] = value
    
    # Second pass: render subject with other metadata available
    if 'subject' in metadata and isinstance(metadata['subject'], str):
        try:
            rendered_value = render_template(metadata['subject'], rendered_metadata, record)
            rendered_metadata['subject'] = rendered_value
            print(f"Debug: subject: '{metadata['subject']}' -> '{rendered_value}'")
        except Exception as e:
            print(f"Warning: Failed to render subject: {e}")
            rendered_metadata['subject'] = metadata['subject']
    
    return rendered_metadata