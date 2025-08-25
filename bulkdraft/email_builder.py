"""
Email building and formatting functionality.
"""

import re
import email.utils
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


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
    msg['User-Agent'] = 'bulkdraft/1.0'
    
    # Add standard email headers that some servers expect
    msg['MIME-Version'] = '1.0'
    msg['X-Mailer'] = 'bulkdraft Python Script'

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