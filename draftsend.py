#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# dependencies:
# pyyaml~=6.0
# markdown~=3.4
# ics~=0.7
# pytz~=2023.3
# jinja2~=3.1

import argparse
import csv
import imaplib
import email
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import yaml
import markdown
import os
from ics import Calendar, Event
from datetime import datetime
import configparser
import pytz
from jinja2 import Template, Environment, BaseLoader

def load_config():
    """
    Load configuration from ~/.config/draftsend.conf
    
    Returns:
        dict: Configuration settings
        
    Raises:
        SystemExit: If config file is missing or invalid
    """
    config_path = os.path.expanduser('~/.config/draftsend.conf')
    if not os.path.exists(config_path):
        print("❌ Configuration file not found!")
        print(f"Please copy the example configuration file:")
        print(f"  cp draftsend.conf.example ~/.config/draftsend.conf")
        print(f"Then edit ~/.config/draftsend.conf with your IMAP settings.")
        exit(1)
    
    config = configparser.ConfigParser()
    try:
        config.read(config_path)
        return config['DEFAULT']
    except Exception as e:
        print(f"❌ Error reading configuration file: {e}")
        print(f"Please check the format of ~/.config/draftsend.conf")
        exit(1)

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

def load_context_file(context_file):
    """
    Load context data from CSV, YAML, or other supported formats.
    
    Args:
        context_file (str): Path to the context data file
        
    Returns:
        list: List of dictionaries containing context data
        
    Raises:
        ValueError: If file format is not supported
    """
    if not context_file or not os.path.exists(context_file):
        return []
    
    ext = os.path.splitext(context_file)[1].lower()
    
    if ext == '.csv':
        with open(context_file, 'r') as file:
            reader = csv.DictReader(file)
            return list(reader)
    elif ext in ['.yml', '.yaml']:
        with open(context_file, 'r') as file:
            data = yaml.safe_load(file)
            if isinstance(data, list):
                return data
            else:
                return [data]
    else:
        raise ValueError(f"Unsupported context file format: {ext}")

def create_ics_file(metadata):
    """
    Create ICS calendar file from event metadata.
    
    Args:
        metadata (dict): Event metadata containing event details
        
    Returns:
        str: Serialized ICS calendar content
    """
    cal = Calendar()
    event = Event()
    event.name = metadata.get('event_name', 'Event')
    
    # Parse the date and apply the timezone
    timezone_str = metadata.get('timezone', 'UTC')
    event_date_str = metadata.get('event_date', '2023-12-01 10:00:00')
    
    # Debug: Check if timezone is properly rendered
    if timezone_str.startswith('{{') and timezone_str.endswith('}}'):
        print(f"Warning: Timezone not properly rendered: {timezone_str}")
        timezone_str = 'UTC'  # Fallback to UTC
    
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        print(f"Warning: Unknown timezone '{timezone_str}', falling back to UTC")
        local_tz = pytz.timezone('UTC')
    
    try:
        naive_datetime = datetime.strptime(event_date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print(f"Warning: Invalid date format '{event_date_str}', using current time")
        naive_datetime = datetime.now()
    
    local_datetime = local_tz.localize(naive_datetime)
    
    event.begin = local_datetime
    event.location = metadata.get('event_location', 'TBD')
    cal.events.add(event)
    return cal.serialize()

def wrap_html_for_email(html_content):
    """
    Wrap HTML content with proper email structure and CSS.
    
    Args:
        html_content (str): HTML content to wrap
        
    Returns:
        str: Complete HTML document with email-compatible styling
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Email</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        h1, h2, h3, h4, h5, h6 {{ color: #333; margin-bottom: 10px; }}
        p {{ margin-bottom: 15px; }}
        strong, b {{ font-weight: bold; }}
        em, i {{ font-style: italic; }}
        ul, ol {{ margin-bottom: 15px; padding-left: 20px; }}
        li {{ margin-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; }}
        td, th {{ padding: 8px; border: 1px solid #ddd; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        img {{ max-width: 100%; height: auto; }}
        a {{ color: #007cba; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

def html_to_plain_text(html_content):
    """
    Convert HTML to plain text for fallback.
    
    Args:
        html_content (str): HTML content to convert
        
    Returns:
        str: Plain text version of the content
    """
    import re
    # Remove HTML tags and convert common elements
    text = re.sub(r'<br[^>]*>', '\n', html_content)
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<h[1-6][^>]*>', '\n', text)
    text = re.sub(r'</h[1-6]>', '\n', text)
    text = re.sub(r'<li[^>]*>', '\n• ', text)
    text = re.sub(r'<[^>]+>', '', text)  # Remove all remaining HTML tags
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up multiple newlines
    return text.strip()

def create_draft_email(config, recipient, subject, html_content, ics_content):
    """
    Create a draft email with HTML content and ICS calendar attachment.
    
    Args:
        config (dict): Configuration settings
        recipient (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML email content
        ics_content (str): ICS calendar content
        
    Returns:
        MIMEMultipart: Complete email message ready for IMAP
    """
    # Outer container for mixed content (text + attachment)
    msg = MIMEMultipart('mixed')
    msg['From'] = config['from_email']
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Add Fastmail-specific headers for sendable drafts
    msg['Message-ID'] = f"<{datetime.now().strftime('%Y%m%d%H%M%S')}.{hash(recipient)}@fastmail>"
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['User-Agent'] = 'DraftSend/1.0'
    
    # Add standard email headers that some servers expect
    msg['MIME-Version'] = '1.0'
    msg['X-Mailer'] = 'DraftSend Python Script'

    # Inner container for alternative text formats
    msg_alternative = MIMEMultipart('alternative')
    
    # Add plain text version
    plain_content = html_to_plain_text(html_content)
    msg_alternative.attach(MIMEText(plain_content, 'plain'))
    
    # Add HTML version with proper email structure
    wrapped_html = wrap_html_for_email(html_content)
    msg_alternative.attach(MIMEText(wrapped_html, 'html'))
    
    msg.attach(msg_alternative)

    # Attach ICS file with proper calendar MIME type and headers
    ics_part = MIMEBase('text', 'calendar')
    ics_part.set_payload(ics_content)
    
    # Set proper calendar headers for better recognition
    ics_part.add_header('Content-Transfer-Encoding', '7bit')
    ics_part.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
    ics_part.add_header('Content-Type', 'text/calendar; charset=utf-8; method=REQUEST; name="invite.ics"')
    
    # Alternative: also add as inline calendar part for some email clients
    ics_inline = MIMEBase('text', 'calendar')
    ics_inline.set_payload(ics_content)
    ics_inline.add_header('Content-Transfer-Encoding', '7bit')
    ics_inline.add_header('Content-Disposition', 'inline')
    ics_inline.add_header('Content-Type', 'text/calendar; charset=utf-8; method=REQUEST')
    
    msg.attach(ics_part)
    msg.attach(ics_inline)

    return msg

def find_drafts_folder(imap_connection):
    """
    Find the correct Drafts folder name for this IMAP server.
    
    Args:
        imap_connection: Active IMAP connection
        
    Returns:
        str: Name of the Drafts folder
    """
    try:
        status, folders = imap_connection.list()
        if status == 'OK':
            folder_list = [folder.decode('utf-8') for folder in folders]
            # Check common draft folder names
            for folder_info in folder_list:
                folder_name = folder_info.split('"')[-2] if '"' in folder_info else folder_info.split()[-1]
                if any(draft_name in folder_name.lower() for draft_name in ['draft', 'brouillon', 'bozza']):
                    print(f"Found Drafts folder: {folder_name}")
                    return folder_name
    except Exception as e:
        print(f"Warning: Could not list folders: {e}")
    
    # Fallback to common names
    return 'Drafts'

def save_draft_to_imap(imap_connection, message):
    """
    Save draft message to IMAP server with proper draft flags.
    
    Args:
        imap_connection: Active IMAP connection
        message: Email message to save as draft
    """
    # Use timezone-aware datetime for IMAP
    now = datetime.now(pytz.UTC)
    
    # Set proper IMAP flags for drafts
    draft_flags = '\\Draft \\Seen'
    
    # Find the correct drafts folder
    drafts_folder = find_drafts_folder(imap_connection)
    
    # Save to Drafts folder with draft flags
    try:
        result = imap_connection.append(drafts_folder, draft_flags, imaplib.Time2Internaldate(now), str(message).encode('utf-8'))
        if result[0] == 'OK':
            print(f"✓ Draft saved to {drafts_folder}")
        else:
            print(f"✗ Failed to save draft to {drafts_folder}: {result[1]}")
    except Exception as e:
        print(f"✗ Error saving draft: {e}")

def test_imap_settings(email, subject, message_content):
    """
    Test IMAP settings by creating a single draft email.
    
    Args:
        email (str): Test recipient email address
        subject (str): Test email subject
        message_content (str): Test email content
        
    Returns:
        bool: True if test successful, False otherwise
    """
    config = load_config()
    
    try:
        # Connect to IMAP server
        imap_conn = imaplib.IMAP4_SSL(config['imap_server'], int(config['imap_port']))
        imap_conn.login(config['imap_username'], config['imap_password'])
        
        # Create draft email with both plain text and HTML versions
        msg = MIMEMultipart('alternative')
        msg['From'] = config['from_email']
        msg['To'] = email
        msg['Subject'] = subject
        
        # Add Fastmail-specific headers for sendable drafts
        msg['Message-ID'] = f"<{datetime.now().strftime('%Y%m%d%H%M%S')}.{hash(email)}@fastmail>"
        msg['Date'] = email.utils.formatdate(localtime=True)
        msg['User-Agent'] = 'DraftSend/1.0'
        msg['MIME-Version'] = '1.0'
        msg['X-Mailer'] = 'DraftSend Python Script'
        
        # Add plain text version
        msg.attach(MIMEText(message_content, 'plain'))
        
        # Add HTML version
        html_message = f"<p>{message_content.replace(chr(10), '<br>')}</p>"
        wrapped_html = wrap_html_for_email(html_message)
        msg.attach(MIMEText(wrapped_html, 'html'))
        
        # Save to drafts folder
        save_draft_to_imap(imap_conn, msg)
        imap_conn.logout()
        
        print(f"✓ Test email successfully created in drafts for: {email}")
        print(f"✓ Subject: {subject}")
        print("✓ IMAP settings are working correctly")
        
    except Exception as e:
        print(f"✗ IMAP test failed: {str(e)}")
        return False
    
    return True

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

def dedupe_records(context_records):
    """
    Remove duplicate email addresses from context records.
    
    Args:
        context_records (list): List of context data dictionaries
        
    Returns:
        list: Deduplicated list of context records
    """
    seen_emails = set()
    deduped_records = []
    for record in context_records:
        email = record.get('email', '').lower().strip()
        if email and email not in seen_emails:
            seen_emails.add(email)
            deduped_records.append(record)
        elif email:
            print(f"Skipping duplicate email: {email} (name: {record.get('first_name', 'unknown')})")
    
    print(f"Processing {len(deduped_records)} unique recipients (removed {len(context_records) - len(deduped_records)} duplicates)")
    return deduped_records

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

def main():
    """
    Main function - parse command line arguments and dispatch to appropriate handler.
    """
    args = parse_command_line()
    
    if args.command == 'test':
        test_imap_settings(args.email, args.subject, args.message)
    elif args.command == 'template':
        process_template_mode(args)

if __name__ == "__main__":
    main()