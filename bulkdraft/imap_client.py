"""
IMAP client functionality for saving drafts and testing connections.
"""

import imaplib
import email.utils
from datetime import datetime
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import load_config
from .email_builder import wrap_html_for_email


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
        msg['User-Agent'] = 'bulkdraft/1.0'
        msg['MIME-Version'] = '1.0'
        msg['X-Mailer'] = 'bulkdraft Python Script'
        
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