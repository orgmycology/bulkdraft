"""
Offline tests for IMAP functionality (testing logic without actual IMAP connections).
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import imaplib
from email.mime.multipart import MIMEMultipart

from draftsend.imap_client import find_drafts_folder, save_draft_to_imap, test_imap_settings


class TestIMAPOffline(unittest.TestCase):
    """Test IMAP functionality offline (mocked connections)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_imap_conn = Mock()
        self.test_message = MIMEMultipart()
        self.test_message['Subject'] = 'Test Subject'

    def test_find_drafts_folder_success(self):
        """Test successful drafts folder detection."""
        # Mock folder list response
        folder_data = [
            b'(\\HasNoChildren \\Drafts) "/" "Drafts"',
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren) "/" "Sent"'
        ]
        self.mock_imap_conn.list.return_value = ('OK', folder_data)
        
        with patch('builtins.print') as mock_print:
            result = find_drafts_folder(self.mock_imap_conn)
            
        self.assertEqual(result, 'Drafts')
        mock_print.assert_called_with('Found Drafts folder: Drafts')

    def test_find_drafts_folder_alternative_name(self):
        """Test finding drafts folder with alternative name."""
        folder_data = [
            b'(\\HasNoChildren) "/" "INBOX.Drafts"',
            b'(\\HasNoChildren) "/" "INBOX"'
        ]
        self.mock_imap_conn.list.return_value = ('OK', folder_data)
        
        with patch('builtins.print'):
            result = find_drafts_folder(self.mock_imap_conn)
            
        self.assertEqual(result, 'INBOX.Drafts')

    def test_find_drafts_folder_fallback(self):
        """Test fallback when no drafts folder found."""
        folder_data = [
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren) "/" "Sent"'
        ]
        self.mock_imap_conn.list.return_value = ('OK', folder_data)
        
        result = find_drafts_folder(self.mock_imap_conn)
        
        self.assertEqual(result, 'Drafts')  # Fallback

    def test_find_drafts_folder_error_handling(self):
        """Test error handling in folder detection."""
        self.mock_imap_conn.list.side_effect = Exception('Connection error')
        
        with patch('builtins.print') as mock_print:
            result = find_drafts_folder(self.mock_imap_conn)
            
        self.assertEqual(result, 'Drafts')  # Fallback
        mock_print.assert_called()
        
        # Check for warning message
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('Could not list folders' in call for call in print_calls))

    @patch('draftsend.imap_client.find_drafts_folder')
    @patch('imaplib.Time2Internaldate')
    @patch('pytz.UTC')
    def test_save_draft_to_imap_success(self, mock_utc, mock_time2internal, mock_find_folder):
        """Test successful draft saving."""
        mock_find_folder.return_value = 'Drafts'
        mock_time2internal.return_value = 'mock_date'
        self.mock_imap_conn.append.return_value = ('OK', None)
        
        with patch('builtins.print') as mock_print:
            save_draft_to_imap(self.mock_imap_conn, self.test_message)
            
        # Check that append was called with correct parameters
        self.mock_imap_conn.append.assert_called_once()
        args = self.mock_imap_conn.append.call_args[0]
        self.assertEqual(args[0], 'Drafts')  # Folder name
        self.assertEqual(args[1], '\\Draft \\Seen')  # Flags
        
        # Check success message
        mock_print.assert_called_with('✓ Draft saved to Drafts')

    @patch('draftsend.imap_client.find_drafts_folder')
    @patch('imaplib.Time2Internaldate')
    def test_save_draft_to_imap_failure(self, mock_time2internal, mock_find_folder):
        """Test draft saving failure."""
        mock_find_folder.return_value = 'Drafts'
        mock_time2internal.return_value = 'mock_date'
        self.mock_imap_conn.append.return_value = ('NO', 'Permission denied')
        
        with patch('builtins.print') as mock_print:
            save_draft_to_imap(self.mock_imap_conn, self.test_message)
            
        # Check error message
        mock_print.assert_called_with('✗ Failed to save draft to Drafts: Permission denied')

    @patch('draftsend.imap_client.find_drafts_folder')
    def test_save_draft_to_imap_exception(self, mock_find_folder):
        """Test exception handling in draft saving."""
        mock_find_folder.return_value = 'Drafts'
        self.mock_imap_conn.append.side_effect = Exception('Connection lost')
        
        with patch('builtins.print') as mock_print:
            save_draft_to_imap(self.mock_imap_conn, self.test_message)
            
        # Check error message
        mock_print.assert_called_with('✗ Error saving draft: Connection lost')

    @patch('draftsend.imap_client.load_config')
    @patch('imaplib.IMAP4_SSL')
    def test_test_imap_settings_success(self, mock_imap_ssl, mock_load_config):
        """Test successful IMAP settings test."""
        # Mock config
        mock_config = {
            'imap_server': 'test.example.com',
            'imap_port': '993',
            'imap_username': 'test@example.com',
            'imap_password': 'password',
            'from_email': 'test@example.com'
        }
        mock_load_config.return_value = mock_config
        
        # Mock IMAP connection
        mock_conn = Mock()
        mock_imap_ssl.return_value = mock_conn
        
        with patch('draftsend.imap_client.save_draft_to_imap') as mock_save:
            with patch('builtins.print') as mock_print:
                result = test_imap_settings('recipient@example.com', 'Test Subject', 'Test message')
                
        self.assertTrue(result)
        
        # Check that connection was made
        mock_imap_ssl.assert_called_once_with('test.example.com', 993)
        mock_conn.login.assert_called_once_with('test@example.com', 'password')
        mock_conn.logout.assert_called_once()
        
        # Check that draft was saved
        mock_save.assert_called_once()
        
        # Check success messages
        success_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('successfully created' in call for call in success_calls))

    @patch('draftsend.imap_client.load_config')
    @patch('imaplib.IMAP4_SSL')
    def test_test_imap_settings_connection_failure(self, mock_imap_ssl, mock_load_config):
        """Test IMAP settings test with connection failure."""
        mock_load_config.return_value = {
            'imap_server': 'test.example.com',
            'imap_port': '993',
            'imap_username': 'test@example.com',
            'imap_password': 'password',
            'from_email': 'test@example.com'
        }
        
        # Mock connection failure
        mock_imap_ssl.side_effect = Exception('Connection refused')
        
        with patch('builtins.print') as mock_print:
            result = test_imap_settings('recipient@example.com', 'Test Subject', 'Test message')
            
        self.assertFalse(result)
        
        # Check error message
        error_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('IMAP test failed' in call for call in error_calls))

    @patch('draftsend.imap_client.load_config')
    @patch('imaplib.IMAP4_SSL')
    def test_test_imap_settings_auth_failure(self, mock_imap_ssl, mock_load_config):
        """Test IMAP settings test with authentication failure."""
        mock_load_config.return_value = {
            'imap_server': 'test.example.com',
            'imap_port': '993',
            'imap_username': 'test@example.com',
            'imap_password': 'wrong_password',
            'from_email': 'test@example.com'
        }
        
        mock_conn = Mock()
        mock_conn.login.side_effect = imaplib.IMAP4.error('Authentication failed')
        mock_imap_ssl.return_value = mock_conn
        
        with patch('builtins.print') as mock_print:
            result = test_imap_settings('recipient@example.com', 'Test Subject', 'Test message')
            
        self.assertFalse(result)
        
        # Check that login was attempted
        mock_conn.login.assert_called_once()


if __name__ == '__main__':
    unittest.main()