"""
DraftSend - A Python utility for creating personalized draft emails with calendar invitations.

This package provides functionality for:
- Template-based email generation with Jinja2
- Context data support from CSV/YAML files  
- Calendar invitation (ICS) creation
- IMAP integration for saving drafts
- Email deduplication and filtering
"""

__version__ = "1.0.0"
__author__ = "DraftSend Contributors"

from .config import load_config
from .template import load_content, render_template, render_metadata_templates
from .context import load_context_file, dedupe_records
from .email_builder import create_draft_email, wrap_html_for_email, html_to_plain_text
from .calendar import create_ics_file
from .imap_client import find_drafts_folder, save_draft_to_imap, test_imap_settings
from .cli import parse_command_line, process_template_mode

__all__ = [
    'load_config',
    'load_content', 
    'render_template',
    'render_metadata_templates',
    'load_context_file',
    'dedupe_records', 
    'create_draft_email',
    'wrap_html_for_email',
    'html_to_plain_text',
    'create_ics_file',
    'find_drafts_folder',
    'save_draft_to_imap', 
    'test_imap_settings',
    'parse_command_line',
    'process_template_mode'
]