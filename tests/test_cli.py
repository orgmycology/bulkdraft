"""
Tests for command line interface functionality.
"""

import unittest
import argparse
from unittest.mock import patch, Mock, MagicMock
import sys

from draftsend.cli import parse_command_line, process_template_mode


class TestCLI(unittest.TestCase):
    """Test command line interface functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        """Clean up after tests."""
        sys.argv = self.original_argv

    def test_parse_command_line_template_mode(self):
        """Test parsing template mode arguments."""
        sys.argv = ['draftsend', 'template', 'test.txt', '--context', 'data.csv']
        
        args = parse_command_line()
        
        self.assertEqual(args.command, 'template')
        self.assertEqual(args.template_file, 'test.txt')
        self.assertEqual(args.context, 'data.csv')

    def test_parse_command_line_test_mode(self):
        """Test parsing test mode arguments."""
        sys.argv = ['draftsend', 'test', 'test@example.com', 'Test Subject', 'Test message']
        
        args = parse_command_line()
        
        self.assertEqual(args.command, 'test')
        self.assertEqual(args.email, 'test@example.com')
        self.assertEqual(args.subject, 'Test Subject')
        self.assertEqual(args.message, 'Test message')

    def test_parse_command_line_backward_compatibility(self):
        """Test backward compatibility with old argument format."""
        sys.argv = ['draftsend', 'template.txt', '--context', 'data.csv']
        
        args = parse_command_line()
        
        self.assertEqual(args.command, 'template')
        self.assertEqual(args.template_file, 'template.txt')
        self.assertEqual(args.context, 'data.csv')

    def test_parse_command_line_legacy_csv_flag(self):
        """Test legacy --csv flag support."""
        sys.argv = ['draftsend', 'template', 'test.txt', '--csv', 'data.csv']
        
        args = parse_command_line()
        
        self.assertEqual(args.command, 'template')
        self.assertEqual(args.csv, 'data.csv')

    @patch('draftsend.cli.load_config')
    @patch('draftsend.cli.load_content')
    @patch('draftsend.cli.load_context_file')
    @patch('draftsend.cli.dedupe_records')
    @patch('imaplib.IMAP4_SSL')
    def test_process_template_mode_basic_flow(self, mock_imap_ssl, mock_dedupe, 
                                            mock_load_context, mock_load_content, mock_load_config):
        """Test basic template processing flow."""
        # Mock configuration
        mock_config = {
            'imap_server': 'test.example.com',
            'imap_port': '993',
            'imap_username': 'test@example.com',
            'imap_password': 'password',
            'from_email': 'test@example.com'
        }
        mock_load_config.return_value = mock_config
        
        # Mock template content
        mock_metadata = {'event_name': 'Test Event', 'subject': 'Test Subject'}
        mock_template_content = 'Dear {{ first_name }}, Welcome to {{ event_name }}!'
        mock_load_content.return_value = (mock_metadata, mock_template_content)
        
        # Mock context data
        mock_context_records = [
            {'first_name': 'John', 'email': 'john@example.com', 'include': 'TRUE'}
        ]
        mock_load_context.return_value = mock_context_records
        mock_dedupe.return_value = mock_context_records
        
        # Mock IMAP connection
        mock_conn = Mock()
        mock_imap_ssl.return_value = mock_conn
        
        # Create mock args
        args = Mock()
        args.template_file = 'test.txt'
        args.context = 'data.csv'
        args.csv = None
        
        with patch('draftsend.cli.render_metadata_templates') as mock_render_meta:
            with patch('draftsend.cli.render_template') as mock_render:
                with patch('draftsend.cli.markdown.markdown') as mock_markdown:
                    with patch('draftsend.cli.create_ics_file') as mock_ics:
                        with patch('draftsend.cli.create_draft_email') as mock_create_email:
                            with patch('draftsend.cli.save_draft_to_imap') as mock_save:
                                with patch('builtins.print'):
                                    
                                    # Set up mocks
                                    mock_render_meta.return_value = mock_metadata
                                    mock_render.return_value = 'Rendered content'
                                    mock_markdown.return_value = '<p>Rendered content</p>'
                                    mock_ics.return_value = 'ICS content'
                                    mock_create_email.return_value = Mock()
                                    
                                    # Run the function
                                    process_template_mode(args)
        
        # Verify the flow
        mock_load_config.assert_called_once()
        mock_load_content.assert_called_once_with('test.txt')
        mock_load_context.assert_called_once_with('data.csv')
        mock_dedupe.assert_called_once()
        mock_imap_ssl.assert_called_once_with('test.example.com', 993)
        mock_conn.login.assert_called_once()
        mock_conn.logout.assert_called_once()

    @patch('draftsend.cli.load_config')
    @patch('draftsend.cli.load_content')  
    @patch('draftsend.cli.load_context_file')
    @patch('draftsend.cli.dedupe_records')
    @patch('imaplib.IMAP4_SSL')
    def test_process_template_mode_include_filtering(self, mock_imap_ssl, mock_dedupe,
                                                   mock_load_context, mock_load_content, mock_load_config):
        """Test include/exclude filtering in template processing."""
        # Mock data with include filtering
        mock_config = {'from_email': 'test@example.com', 'imap_server': 'test.com', 'imap_port': '993', 
                      'imap_username': 'test', 'imap_password': 'pass'}
        mock_load_config.return_value = mock_config
        mock_load_content.return_value = ({'event_name': 'Test'}, 'Content')
        
        mock_context_records = [
            {'first_name': 'John', 'email': 'john@example.com', 'include': 'TRUE'},
            {'first_name': 'Jane', 'email': 'jane@example.com', 'include': 'FALSE'},
            {'first_name': 'Bob', 'email': 'bob@example.com', 'include': 'true'}
        ]
        mock_load_context.return_value = mock_context_records
        mock_dedupe.return_value = mock_context_records
        
        mock_conn = Mock()
        mock_imap_ssl.return_value = mock_conn
        
        args = Mock()
        args.template_file = 'test.txt'
        args.context = 'data.csv'
        args.csv = None
        
        with patch('draftsend.cli.render_metadata_templates') as mock_render_meta:
            with patch('draftsend.cli.render_template'):
                with patch('draftsend.cli.markdown.markdown'):
                    with patch('draftsend.cli.create_ics_file'):
                        with patch('draftsend.cli.create_draft_email'):
                            with patch('draftsend.cli.save_draft_to_imap') as mock_save:
                                with patch('builtins.print') as mock_print:
                                    
                                    mock_render_meta.return_value = {'event_name': 'Test', 'subject': 'Test'}
                                    
                                    process_template_mode(args)
        
        # Should only process John and Bob (include=TRUE/true), skip Jane (include=FALSE)
        self.assertEqual(mock_save.call_count, 2)
        
        # Check that skip message was printed for Jane
        print_calls = [str(call) for call in mock_print.call_args_list]
        skip_calls = [call for call in print_calls if 'Skipping' in call and 'Jane' in call]
        self.assertTrue(len(skip_calls) > 0)

    @patch('draftsend.cli.load_config')
    @patch('draftsend.cli.load_content')
    @patch('draftsend.cli.load_context_file')
    def test_process_template_mode_no_context_file(self, mock_load_context, mock_load_content, mock_load_config):
        """Test template processing without context file."""
        mock_config = {'from_email': 'test@example.com', 'imap_server': 'test.com', 'imap_port': '993',
                      'imap_username': 'test', 'imap_password': 'pass'}
        mock_load_config.return_value = mock_config
        mock_load_content.return_value = ({'event_name': 'Test'}, 'Content')
        mock_load_context.return_value = [{}]  # Empty context
        
        args = Mock()
        args.template_file = 'test.txt'
        args.context = None
        args.csv = None
        
        with patch('draftsend.cli.dedupe_records') as mock_dedupe:
            with patch('imaplib.IMAP4_SSL') as mock_imap_ssl:
                mock_conn = Mock()
                mock_imap_ssl.return_value = mock_conn
                mock_dedupe.return_value = [{}]
                
                with patch('draftsend.cli.render_metadata_templates'):
                    with patch('draftsend.cli.render_template'):
                        with patch('draftsend.cli.markdown.markdown'):
                            with patch('draftsend.cli.create_ics_file'):
                                with patch('draftsend.cli.create_draft_email'):
                                    with patch('draftsend.cli.save_draft_to_imap'):
                                        with patch('builtins.print'):
                                            process_template_mode(args)
        
        # Should use empty context when no file provided
        mock_load_context.assert_not_called()

    def test_parse_command_line_help_template(self):
        """Test help text for template command."""
        sys.argv = ['draftsend', 'template', '--help']
        
        with self.assertRaises(SystemExit):
            with patch('sys.stderr'):  # Suppress help output
                parse_command_line()

    def test_parse_command_line_help_test(self):
        """Test help text for test command."""
        sys.argv = ['draftsend', 'test', '--help']
        
        with self.assertRaises(SystemExit):
            with patch('sys.stderr'):  # Suppress help output
                parse_command_line()


if __name__ == '__main__':
    unittest.main()