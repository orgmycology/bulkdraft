"""
Tests for configuration management.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
import configparser

from bulkdraft.config import load_config


class TestConfig(unittest.TestCase):
    """Test configuration loading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config_content = """
[DEFAULT]
imap_server=test.example.com
imap_port=993
imap_username=test@example.com
imap_password=testpass
from_email=test@example.com
"""

    @patch('os.path.exists')
    @patch('builtins.exit')
    def test_load_config_missing_file(self, mock_exit, mock_exists):
        """Test load_config when config file doesn't exist."""
        mock_exists.return_value = False
        
        with patch('builtins.print') as mock_print:
            load_config()
            
        mock_exit.assert_called_once_with(1)
        mock_print.assert_called()
        
        # Check that helpful error message is printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        self.assertTrue(any('Configuration file not found' in call for call in print_calls))
        self.assertTrue(any('cp bulkdraft.conf.example' in call for call in print_calls))

    @patch('os.path.exists')
    def test_load_config_success(self, mock_exists):
        """Test successful config loading."""
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data=self.test_config_content)):
            config = load_config()
            
        self.assertEqual(config['imap_server'], 'test.example.com')
        self.assertEqual(config['imap_port'], '993')
        self.assertEqual(config['imap_username'], 'test@example.com')
        self.assertEqual(config['from_email'], 'test@example.com')

    @patch('os.path.exists')
    @patch('builtins.exit')
    def test_load_config_invalid_format(self, mock_exit, mock_exists):
        """Test load_config with invalid config format."""
        mock_exists.return_value = True
        
        invalid_config = "invalid config content"
        
        with patch('builtins.open', mock_open(read_data=invalid_config)):
            with patch('builtins.print') as mock_print:
                load_config()
                
        mock_exit.assert_called_once_with(1)
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        self.assertTrue(any('Error reading configuration file' in call for call in print_calls))

    @patch('os.path.expanduser')
    def test_config_path_expansion(self, mock_expanduser):
        """Test that config path is properly expanded."""
        mock_expanduser.return_value = '/home/user/.config/bulkdraft.conf'
        
        with patch('os.path.exists', return_value=False):
            with patch('builtins.exit'):
                with patch('builtins.print'):
                    load_config()
                    
        mock_expanduser.assert_called_once_with('~/.config/bulkdraft.conf')


if __name__ == '__main__':
    unittest.main()