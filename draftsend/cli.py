"""
Command line interface and main processing logic.
"""

import argparse
import imaplib
import markdown

from .config import load_config
from .template import load_content, render_template, render_metadata_templates
from .context import load_context_file, dedupe_records
from .email_builder import create_draft_email
from .calendar import create_ics_file
from .imap_client import save_draft_to_imap


def parse_command_line():
    """
    Parse command line arguments and return parsed args.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Create draft emails from a template file and context data.')
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Template command (default behavior)
    template_parser = subparsers.add_parser('template', help='Process template with context data')
    template_parser.add_argument('template_file', help='Template file containing email content with YAML metadata')
    template_parser.add_argument('--context', help='Context data file (CSV/YAML) for template variables')
    template_parser.add_argument('--csv', help='CSV file containing recipient data (deprecated, use --context)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test IMAP settings with a single email')
    test_parser.add_argument('email', help='Recipient email address')
    test_parser.add_argument('subject', help='Email subject')
    test_parser.add_argument('message', help='Email message content')
    
    # For backward compatibility, if no subcommand is given, assume template mode
    args = parser.parse_args()
    if args.command is None:
        # Parse as old-style arguments
        parser = argparse.ArgumentParser(description='Create draft emails from a template file and context data.')
        parser.add_argument('template_file', help='Template file containing email content with YAML metadata')
        parser.add_argument('--context', help='Context data file (CSV/YAML) for template variables')
        parser.add_argument('--csv', help='CSV file containing recipient data (deprecated, use --context)')
        args = parser.parse_args()
        args.command = 'template'
    
    return args


def process_template_mode(args):
    """
    Process template mode: generate draft emails from template and context data.
    
    Args:
        args: Parsed command line arguments
    """
    config = load_config()
    metadata, template_content = load_content(args.template_file)

    # Load context data (prioritize --context, fallback to --csv for backward compatibility)
    context_file = args.context or args.csv
    context_records = load_context_file(context_file) if context_file else [{}]

    # Dedupe by email address to prevent multiple reminders
    deduped_records = dedupe_records(context_records)

    imap_conn = imaplib.IMAP4_SSL(config['imap_server'], int(config['imap_port']))
    imap_conn.login(config['imap_username'], config['imap_password'])

    for record in deduped_records:
        # Check if record should be included (skip if include column exists and is not TRUE)
        if 'include' in record and record['include'].upper() != 'TRUE':
            print(f"Skipping {record.get('first_name', record.get('email', 'unknown'))}: include = {record['include']}")
            continue
        
        # Render metadata templates to get actual values
        rendered_metadata = render_metadata_templates(metadata, record)
        
        # Render the template content with both rendered metadata and record data
        rendered_content = render_template(template_content, rendered_metadata, record)
        
        # Convert markdown to HTML with email-friendly extensions
        html_content = markdown.markdown(
            rendered_content,
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',  # Convert newlines to <br> tags
                'markdown.extensions.fenced_code'
            ],
            output_format='html5'
        )
        
        # Create ICS file with already rendered metadata
        ics_content = create_ics_file(rendered_metadata)
        
        # Get recipient email and subject
        recipient_email = record.get('email', config.get('default_email', 'test@example.com'))
        subject = rendered_metadata.get('subject', rendered_metadata.get('event_name', 'Event Invitation'))
        
        draft_email = create_draft_email(config, recipient_email, subject, html_content, ics_content)
        save_draft_to_imap(imap_conn, draft_email)
        
        recipient_name = record.get('first_name', recipient_email)
        print(f"Draft email created for: {recipient_name} ({recipient_email})")

    imap_conn.logout()
    print("All draft emails have been created and saved to the IMAP server.")