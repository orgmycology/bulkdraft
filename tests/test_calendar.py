"""
Tests for calendar (ICS) functionality.
"""

import unittest
from datetime import datetime
from unittest.mock import patch
import pytz

from bulkdraft.calendar import create_ics_file


class TestCalendar(unittest.TestCase):
    """Test calendar functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_metadata = {
            'event_name': 'Test Event',
            'event_date': '2023-12-01 10:00:00',
            'event_location': 'Conference Room A',
            'timezone': 'America/New_York'
        }

    def test_create_ics_file_basic(self):
        """Test basic ICS file creation."""
        result = create_ics_file(self.test_metadata)
        
        # Should be valid ICS content
        self.assertIn('BEGIN:VCALENDAR', result)
        self.assertIn('END:VCALENDAR', result)
        self.assertIn('BEGIN:VEVENT', result)
        self.assertIn('END:VEVENT', result)
        
        # Should contain event details
        self.assertIn('Test Event', result)
        self.assertIn('Conference Room A', result)

    def test_create_ics_file_with_defaults(self):
        """Test ICS file creation with default values."""
        minimal_metadata = {}
        
        with patch('builtins.print'):  # Suppress warnings
            result = create_ics_file(minimal_metadata)
        
        self.assertIn('BEGIN:VCALENDAR', result)
        self.assertIn('Event', result)  # Default event name

    def test_create_ics_file_timezone_handling(self):
        """Test timezone handling in ICS creation."""
        result = create_ics_file(self.test_metadata)
        
        # Should handle timezone properly (no error should be raised)
        self.assertIn('BEGIN:VEVENT', result)

    def test_create_ics_file_invalid_timezone(self):
        """Test handling of invalid timezone."""
        invalid_metadata = self.test_metadata.copy()
        invalid_metadata['timezone'] = 'Invalid/Timezone'
        
        with patch('builtins.print') as mock_print:
            result = create_ics_file(invalid_metadata)
            
        # Should fallback to UTC and print warning
        self.assertIn('BEGIN:VEVENT', result)
        mock_print.assert_called()
        
        # Check for warning message
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('Unknown timezone' in call for call in print_calls))

    def test_create_ics_file_invalid_date_format(self):
        """Test handling of invalid date format."""
        invalid_metadata = self.test_metadata.copy()
        invalid_metadata['event_date'] = 'invalid-date-format'
        
        with patch('builtins.print') as mock_print:
            result = create_ics_file(invalid_metadata)
            
        # Should fallback and print warning
        self.assertIn('BEGIN:VEVENT', result)
        mock_print.assert_called()
        
        # Check for warning message
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('Invalid date format' in call for call in print_calls))

    def test_create_ics_file_template_string_timezone(self):
        """Test handling of unrendered template string in timezone."""
        template_metadata = self.test_metadata.copy()
        template_metadata['timezone'] = '{{ timezone | default("UTC") }}'
        
        with patch('builtins.print') as mock_print:
            result = create_ics_file(template_metadata)
            
        # Should detect unrendered template and fallback to UTC
        self.assertIn('BEGIN:VEVENT', result)
        mock_print.assert_called()
        
        # Check for warning message
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('not properly rendered' in call for call in print_calls))

    def test_create_ics_file_all_fields(self):
        """Test ICS creation with all metadata fields populated."""
        complete_metadata = {
            'event_name': 'Annual Conference 2023',
            'event_date': '2023-12-15 14:30:00',
            'event_location': 'San Francisco Convention Center',
            'timezone': 'America/Los_Angeles'
        }
        
        result = create_ics_file(complete_metadata)
        
        # Verify all fields are included
        self.assertIn('Annual Conference 2023', result)
        self.assertIn('San Francisco Convention Center', result)
        
        # Should be valid ICS structure
        lines = result.strip().split('\n')
        self.assertTrue(lines[0].startswith('BEGIN:VCALENDAR'))
        self.assertTrue(lines[-1].startswith('END:VCALENDAR'))

    @patch('bulkdraft.calendar.datetime')
    def test_create_ics_file_datetime_fallback(self, mock_datetime):
        """Test datetime fallback when date parsing fails."""
        mock_now = datetime(2023, 12, 1, 15, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = ValueError("Invalid format")
        
        invalid_metadata = self.test_metadata.copy()
        invalid_metadata['event_date'] = 'completely-invalid'
        
        with patch('builtins.print'):
            result = create_ics_file(invalid_metadata)
            
        # Should use current time as fallback
        self.assertIn('BEGIN:VEVENT', result)

    def test_create_ics_file_timezone_localization(self):
        """Test proper timezone localization."""
        # Test with different timezones
        timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']
        
        for tz in timezones:
            metadata = self.test_metadata.copy()
            metadata['timezone'] = tz
            
            result = create_ics_file(metadata)
            
            # Should not raise exceptions and produce valid ICS
            self.assertIn('BEGIN:VCALENDAR', result)
            self.assertIn('Test Event', result)


if __name__ == '__main__':
    unittest.main()