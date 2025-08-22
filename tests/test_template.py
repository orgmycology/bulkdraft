"""
Tests for template processing functionality.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, mock_open

from draftsend.template import load_content, render_template, render_metadata_templates


class TestTemplate(unittest.TestCase):
    """Test template processing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_template = """---
event_name: "{{ event_name | default('Test Event') }}"
event_date: "{{ event_date | default('2023-12-01 10:00:00') }}"
subject: "Reminder: {{ event_name | default('Test Event') }}"
---

Dear {{ first_name | default('Participant') }},

You're invited to {{ event_name }} on {{ event_date }}.

Best regards,
Test Team"""

        self.test_metadata = {
            'event_name': '{{ event_name | default("Test Event") }}',
            'event_date': '{{ event_date | default("2023-12-01 10:00:00") }}',
            'subject': 'Reminder: {{ event_name | default("Test Event") }}'
        }

        self.test_context = {
            'first_name': 'John',
            'email': 'john@example.com'
        }

    def test_load_content(self):
        """Test loading template content and metadata."""
        with patch('builtins.open', mock_open(read_data=self.test_template)):
            metadata, content = load_content('test_template.txt')
            
        self.assertIn('event_name', metadata)
        self.assertIn('event_date', metadata)
        self.assertIn('subject', metadata)
        self.assertIn('Dear {{ first_name', content)
        self.assertIn('You\'re invited to', content)

    def test_render_template_with_defaults(self):
        """Test template rendering with Jinja2 defaults."""
        template_content = "Hello {{ name | default('World') }}!"
        
        result = render_template(template_content, {}, {})
        
        self.assertEqual(result, "Hello World!")

    def test_render_template_with_context(self):
        """Test template rendering with context data."""
        template_content = "Hello {{ name | default('World') }}!"
        context = {'name': 'John'}
        
        result = render_template(template_content, {}, context)
        
        self.assertEqual(result, "Hello John!")

    def test_render_template_with_metadata(self):
        """Test template rendering with resolved metadata."""
        template_content = "Event: {{ event_name }}"
        metadata = {'event_name': 'Test Event'}
        
        result = render_template(template_content, metadata, {})
        
        self.assertEqual(result, "Event: Test Event")

    def test_render_template_context_priority(self):
        """Test that context data overrides metadata."""
        template_content = "Name: {{ name }}"
        metadata = {'name': 'Metadata Name'}
        context = {'name': 'Context Name'}
        
        result = render_template(template_content, metadata, context)
        
        self.assertEqual(result, "Name: Context Name")

    def test_render_metadata_templates_basic(self):
        """Test rendering metadata templates."""
        metadata = {
            'event_name': '{{ event_name | default("Test Event") }}',
            'event_date': '{{ event_date | default("2023-12-01 10:00:00") }}'
        }
        context = {}
        
        with patch('builtins.print'):  # Suppress debug output
            result = render_metadata_templates(metadata, context)
            
        self.assertEqual(result['event_name'], 'Test Event')
        self.assertEqual(result['event_date'], '2023-12-01 10:00:00')

    def test_render_metadata_templates_with_context(self):
        """Test rendering metadata templates with context override."""
        metadata = {
            'event_name': '{{ event_name | default("Default Event") }}'
        }
        context = {'event_name': 'Override Event'}
        
        with patch('builtins.print'):  # Suppress debug output
            result = render_metadata_templates(metadata, context)
            
        self.assertEqual(result['event_name'], 'Override Event')

    def test_render_metadata_templates_subject_dependency(self):
        """Test that subject template can reference other metadata."""
        metadata = {
            'event_name': '{{ event_name | default("Test Event") }}',
            'subject': 'Reminder: {{ event_name }}'
        }
        context = {}
        
        with patch('builtins.print'):  # Suppress debug output
            result = render_metadata_templates(metadata, context)
            
        self.assertEqual(result['event_name'], 'Test Event')
        self.assertEqual(result['subject'], 'Reminder: Test Event')

    def test_render_metadata_templates_error_handling(self):
        """Test error handling in metadata template rendering."""
        metadata = {
            'invalid_template': '{{ invalid_syntax }'  # Missing closing brace
        }
        
        with patch('builtins.print') as mock_print:
            result = render_metadata_templates(metadata, {})
            
        # Should fallback to original value on error
        self.assertEqual(result['invalid_template'], '{{ invalid_syntax }')
        
        # Should print warning
        mock_print.assert_called()
        warning_calls = [call for call in mock_print.call_args_list if 'Warning' in str(call)]
        self.assertTrue(len(warning_calls) > 0)

    def test_render_template_ignores_template_strings_in_metadata(self):
        """Test that template strings in metadata don't cause circular references."""
        template_content = "Hello {{ name }}!"
        metadata = {
            'name': '{{ name | default("World") }}',  # This should be ignored
            'other': 'Other Value'
        }
        
        result = render_template(template_content, metadata, {})
        
        # Should use Jinja2 default since template string is ignored
        self.assertEqual(result, "Hello !")


if __name__ == '__main__':
    unittest.main()