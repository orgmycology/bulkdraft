"""
Tests for email building functionality.
"""

import unittest
from email.mime.multipart import MIMEMultipart
from unittest.mock import patch

from draftsend.email_builder import (
    wrap_html_for_email, 
    html_to_plain_text, 
    create_draft_email
)


class TestEmailBuilder(unittest.TestCase):
    """Test email building functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_html = "<h1>Test Event</h1><p>You're invited to our event.</p>"
        self.test_config = {
            'from_email': 'test@example.com',
            'imap_server': 'test.example.com'
        }
        self.test_ics_content = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test Event
DTSTART:20231201T100000Z
END:VEVENT
END:VCALENDAR"""

    def test_wrap_html_for_email(self):
        """Test HTML wrapping for email compatibility."""
        result = wrap_html_for_email(self.test_html)
        
        # Should contain DOCTYPE and html structure
        self.assertIn('<!DOCTYPE html>', result)
        self.assertIn('<html lang="en">', result)
        self.assertIn('<head>', result)
        self.assertIn('<body>', result)
        
        # Should include meta tags
        self.assertIn('charset="UTF-8"', result)
        self.assertIn('viewport', result)
        
        # Should include CSS styles
        self.assertIn('<style>', result)
        self.assertIn('font-family: Arial', result)
        
        # Should contain original content
        self.assertIn(self.test_html, result)

    def test_html_to_plain_text_basic(self):
        """Test basic HTML to plain text conversion."""
        html = "<p>Hello world</p>"
        result = html_to_plain_text(html)
        
        self.assertEqual(result.strip(), "Hello world")

    def test_html_to_plain_text_headings(self):
        """Test HTML heading conversion."""
        html = "<h1>Main Title</h1><h2>Subtitle</h2><p>Content</p>"
        result = html_to_plain_text(html)
        
        self.assertIn("Main Title", result)
        self.assertIn("Subtitle", result)
        self.assertIn("Content", result)
        # Should have newlines before headings
        lines = result.strip().split('\n')
        self.assertTrue(len(lines) >= 3)

    def test_html_to_plain_text_lists(self):
        """Test HTML list conversion to bullet points."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = html_to_plain_text(html)
        
        self.assertIn("• Item 1", result)
        self.assertIn("• Item 2", result)

    def test_html_to_plain_text_line_breaks(self):
        """Test line break conversion."""
        html = "Line 1<br>Line 2<br/>Line 3"
        result = html_to_plain_text(html)
        
        lines = result.strip().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertIn("Line 1", lines)
        self.assertIn("Line 2", lines)
        self.assertIn("Line 3", lines)

    def test_html_to_plain_text_paragraph_spacing(self):
        """Test paragraph spacing in plain text."""
        html = "<p>Paragraph 1</p><p>Paragraph 2</p>"
        result = html_to_plain_text(html)
        
        # Should have proper spacing between paragraphs
        self.assertIn("Paragraph 1", result)
        self.assertIn("Paragraph 2", result)

    def test_html_to_plain_text_strips_tags(self):
        """Test that all HTML tags are removed."""
        html = '<div class="test"><span style="color:red">Text</span><a href="#">Link</a></div>'
        result = html_to_plain_text(html)
        
        self.assertEqual(result.strip(), "TextLink")
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)

    def test_create_draft_email_structure(self):
        """Test draft email structure and headers."""
        result = create_draft_email(
            self.test_config, 
            'recipient@example.com', 
            'Test Subject',
            self.test_html,
            self.test_ics_content
        )
        
        # Should be MIMEMultipart
        self.assertIsInstance(result, MIMEMultipart)
        
        # Check basic headers
        self.assertEqual(result['From'], 'test@example.com')
        self.assertEqual(result['To'], 'recipient@example.com')
        self.assertEqual(result['Subject'], 'Test Subject')
        
        # Check Fastmail-specific headers
        self.assertIn('Message-ID', result)
        self.assertIn('Date', result)
        self.assertEqual(result['User-Agent'], 'DraftSend/1.0')
        self.assertEqual(result['MIME-Version'], '1.0')
        self.assertEqual(result['X-Mailer'], 'DraftSend Python Script')

    def test_create_draft_email_mime_structure(self):
        """Test MIME structure of draft email."""
        result = create_draft_email(
            self.test_config, 
            'recipient@example.com', 
            'Test Subject',
            self.test_html,
            self.test_ics_content
        )
        
        # Should have multiple parts
        parts = result.get_payload()
        self.assertTrue(len(parts) >= 2)
        
        # First part should be multipart/alternative (HTML + plain text)
        alternative_part = parts[0]
        self.assertEqual(alternative_part.get_content_type(), 'multipart/alternative')
        
        # Should have plain text and HTML versions
        text_parts = alternative_part.get_payload()
        self.assertEqual(len(text_parts), 2)
        
        content_types = [part.get_content_type() for part in text_parts]
        self.assertIn('text/plain', content_types)
        self.assertIn('text/html', content_types)

    def test_create_draft_email_ics_attachments(self):
        """Test ICS calendar attachments."""
        result = create_draft_email(
            self.test_config, 
            'recipient@example.com', 
            'Test Subject',
            self.test_html,
            self.test_ics_content
        )
        
        parts = result.get_payload()
        
        # Should have ICS attachments
        ics_parts = [part for part in parts if part.get_content_type() == 'text/calendar']
        self.assertEqual(len(ics_parts), 2)  # Attachment and inline versions
        
        # Check attachment headers
        attachment_part = None
        inline_part = None
        
        for part in ics_parts:
            if 'attachment' in part.get('Content-Disposition', ''):
                attachment_part = part
            elif 'inline' in part.get('Content-Disposition', ''):
                inline_part = part
                
        self.assertIsNotNone(attachment_part)
        self.assertIsNotNone(inline_part)
        
        # Check specific headers
        self.assertIn('filename="invite.ics"', attachment_part.get('Content-Disposition', ''))
        self.assertIn('method=REQUEST', attachment_part.get('Content-Type', ''))

    @patch('draftsend.email_builder.datetime')
    def test_create_draft_email_message_id(self, mock_datetime):
        """Test Message-ID generation."""
        mock_datetime.now.return_value.strftime.return_value = '20231201120000'
        
        result = create_draft_email(
            self.test_config, 
            'recipient@example.com', 
            'Test Subject',
            self.test_html,
            self.test_ics_content
        )
        
        message_id = result['Message-ID']
        self.assertIn('20231201120000', message_id)
        self.assertIn('@fastmail>', message_id)

    def test_create_draft_email_content_preservation(self):
        """Test that HTML content is preserved in email."""
        result = create_draft_email(
            self.test_config, 
            'recipient@example.com', 
            'Test Subject',
            self.test_html,
            self.test_ics_content
        )
        
        # Get the HTML part
        alternative_part = result.get_payload()[0]
        text_parts = alternative_part.get_payload()
        html_part = next(part for part in text_parts if part.get_content_type() == 'text/html')
        
        html_content = html_part.get_payload()
        self.assertIn('Test Event', html_content)
        self.assertIn('You\'re invited', html_content)
        # Should be wrapped with email HTML structure
        self.assertIn('<!DOCTYPE html>', html_content)


if __name__ == '__main__':
    unittest.main()