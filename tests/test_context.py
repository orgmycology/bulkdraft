"""
Tests for context data processing functionality.
"""

import unittest
import tempfile
import os
import csv
import yaml
from unittest.mock import patch, mock_open

from bulkdraft.context import load_context_file, dedupe_records


class TestContext(unittest.TestCase):
    """Test context data processing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_csv_content = "first_name,last_name,email\nJohn,Doe,john@example.com\nJane,Smith,jane@example.com"
        
        self.test_yaml_content = """
- first_name: John
  last_name: Doe
  email: john@example.com
- first_name: Jane
  last_name: Smith
  email: jane@example.com
"""

        self.test_records = [
            {'first_name': 'John', 'email': 'john@example.com'},
            {'first_name': 'Jane', 'email': 'jane@example.com'},
            {'first_name': 'Duplicate', 'email': 'john@example.com'},  # Duplicate email
            {'first_name': 'Bob', 'email': 'bob@example.com'},
            {'first_name': 'Another', 'email': 'JOHN@EXAMPLE.COM'},  # Case variation
        ]

    def test_load_context_file_nonexistent(self):
        """Test loading nonexistent context file returns empty list."""
        result = load_context_file('nonexistent.csv')
        self.assertEqual(result, [])

    def test_load_context_file_none(self):
        """Test loading None context file returns empty list."""
        result = load_context_file(None)
        self.assertEqual(result, [])

    @patch('os.path.exists')
    def test_load_context_file_csv(self, mock_exists):
        """Test loading CSV context file."""
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data=self.test_csv_content)):
            result = load_context_file('test.csv')
            
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['first_name'], 'John')
        self.assertEqual(result[0]['email'], 'john@example.com')
        self.assertEqual(result[1]['first_name'], 'Jane')

    @patch('os.path.exists')
    def test_load_context_file_yaml_list(self, mock_exists):
        """Test loading YAML context file with list format."""
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data=self.test_yaml_content)):
            result = load_context_file('test.yaml')
            
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['first_name'], 'John')
        self.assertEqual(result[1]['first_name'], 'Jane')

    @patch('os.path.exists')
    def test_load_context_file_yaml_single_object(self, mock_exists):
        """Test loading YAML context file with single object."""
        mock_exists.return_value = True
        single_yaml = "first_name: John\nemail: john@example.com"
        
        with patch('builtins.open', mock_open(read_data=single_yaml)):
            result = load_context_file('test.yml')
            
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['first_name'], 'John')

    @patch('os.path.exists')
    def test_load_context_file_unsupported_format(self, mock_exists):
        """Test loading unsupported file format raises ValueError."""
        mock_exists.return_value = True
        
        with self.assertRaises(ValueError) as context:
            load_context_file('test.txt')
            
        self.assertIn('Unsupported context file format', str(context.exception))

    def test_dedupe_records_basic(self):
        """Test basic email deduplication."""
        with patch('builtins.print') as mock_print:
            result = dedupe_records(self.test_records)
            
        # Should keep first occurrence of each email
        self.assertEqual(len(result), 3)  # John, Jane, Bob
        
        emails = [record['email'] for record in result]
        self.assertIn('john@example.com', emails)
        self.assertIn('jane@example.com', emails)
        self.assertIn('bob@example.com', emails)
        
        # Check that duplicate messages were printed
        mock_print.assert_called()
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('duplicate email' in call.lower() for call in print_calls))

    def test_dedupe_records_case_insensitive(self):
        """Test that deduplication is case-insensitive."""
        with patch('builtins.print'):
            result = dedupe_records(self.test_records)
            
        # Should dedupe john@example.com and JOHN@EXAMPLE.COM
        emails = [record['email'].lower() for record in result]
        self.assertEqual(emails.count('john@example.com'), 1)

    def test_dedupe_records_empty_emails(self):
        """Test deduplication handles empty emails properly."""
        records_with_empty = [
            {'first_name': 'John', 'email': 'john@example.com'},
            {'first_name': 'NoEmail1', 'email': ''},
            {'first_name': 'NoEmail2', 'email': ''},
            {'first_name': 'NoEmail3'},  # Missing email key
        ]
        
        with patch('builtins.print'):
            result = dedupe_records(records_with_empty)
            
        # Should only keep John (others have no email)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['first_name'], 'John')

    def test_dedupe_records_whitespace_handling(self):
        """Test that whitespace is stripped during deduplication."""
        records_with_spaces = [
            {'first_name': 'John', 'email': 'john@example.com'},
            {'first_name': 'Duplicate', 'email': ' john@example.com '},  # With spaces
            {'first_name': 'Bob', 'email': 'bob@example.com'},
        ]
        
        with patch('builtins.print'):
            result = dedupe_records(records_with_spaces)
            
        self.assertEqual(len(result), 2)  # John and Bob, duplicate removed

    def test_dedupe_records_preserves_first_occurrence(self):
        """Test that deduplication preserves the first occurrence of each email."""
        records = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'test@example.com'},
            {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'test@example.com'},
        ]
        
        with patch('builtins.print'):
            result = dedupe_records(records)
            
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['first_name'], 'John')  # First occurrence
        self.assertEqual(result[0]['last_name'], 'Doe')


if __name__ == '__main__':
    unittest.main()