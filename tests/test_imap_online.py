"""
Online tests for IMAP functionality (requires actual IMAP configuration).

These tests will only run if IMAP settings are configured and accessible.
They create actual draft emails in the IMAP server for integration testing.
"""

import unittest
import os
from unittest import skip

from bulkdraft.config import load_config
from bulkdraft.imap_client import test_imap_settings
from bulkdraft.email_builder import create_draft_email
from bulkdraft.calendar import create_ics_file
from bulkdraft.imap_client import save_draft_to_imap
import imaplib


def check_imap_config():
    """Check if IMAP configuration is available for testing."""
    try:
        config_path = os.path.expanduser('~/.config/bulkdraft.conf')
        return os.path.exists(config_path)
    except:
        return False


@unittest.skipUnless(check_imap_config(), "IMAP configuration not found - skipping online tests")
class TestIMAPOnline(unittest.TestCase):
    """Online IMAP tests that require actual IMAP server access."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        try:
            cls.config = load_config()
            cls.test_email = cls.config.get('from_email', 'test@example.com')
        except SystemExit:
            raise unittest.SkipTest("IMAP configuration not available")

    def setUp(self):
        """Set up test fixtures."""
        self.test_subject = "bulkdraft Online Test - Safe to Delete"
        self.test_message = "This is a test message from the bulkdraft test suite. Safe to delete."

    def test_imap_connection_and_auth(self):
        """Test IMAP connection and authentication."""
        try:
            imap_conn = imaplib.IMAP4_SSL(self.config['imap_server'], int(self.config['imap_port']))
            imap_conn.login(self.config['imap_username'], self.config['imap_password'])
            imap_conn.logout()
            
            # If we get here, connection worked
            self.assertTrue(True)
            
        except Exception as e:
            self.fail(f"IMAP connection failed: {e}")

    def test_imap_test_function(self):
        """Test the test_imap_settings function with real IMAP."""
        result = test_imap_settings(
            self.test_email,
            self.test_subject,
            self.test_message
        )
        
        self.assertTrue(result, "IMAP test should succeed with valid configuration")

    def test_draft_creation_integration(self):
        """Test complete draft creation workflow."""
        # Test metadata
        test_metadata = {
            'event_name': 'Integration Test Event',
            'event_date': '2023-12-01 10:00:00',
            'event_location': 'Test Location',
            'timezone': 'UTC',
            'subject': 'Test Integration Event'
        }
        
        # Create ICS content
        ics_content = create_ics_file(test_metadata)
        
        # Create draft email
        draft_email = create_draft_email(
            self.config,
            self.test_email,
            "bulkdraft Integration Test - Safe to Delete",
            "<h1>Integration Test</h1><p>This is a test email from bulkdraft integration tests.</p>",
            ics_content
        )
        
        # Connect to IMAP and save draft
        try:
            imap_conn = imaplib.IMAP4_SSL(self.config['imap_server'], int(self.config['imap_port']))
            imap_conn.login(self.config['imap_username'], self.config['imap_password'])
            
            save_draft_to_imap(imap_conn, draft_email)
            
            imap_conn.logout()
            
            # If we get here without exception, test passed
            self.assertTrue(True)
            
        except Exception as e:
            self.fail(f"Draft creation integration test failed: {e}")

    def test_drafts_folder_detection(self):
        """Test that drafts folder can be detected on real IMAP server."""
        from bulkdraft.imap_client import find_drafts_folder
        
        try:
            imap_conn = imaplib.IMAP4_SSL(self.config['imap_server'], int(self.config['imap_port']))
            imap_conn.login(self.config['imap_username'], self.config['imap_password'])
            
            drafts_folder = find_drafts_folder(imap_conn)
            
            imap_conn.logout()
            
            # Should return a folder name
            self.assertIsInstance(drafts_folder, str)
            self.assertTrue(len(drafts_folder) > 0)
            
        except Exception as e:
            self.fail(f"Drafts folder detection failed: {e}")

    def test_multiple_draft_creation(self):
        """Test creating multiple drafts in sequence."""
        test_messages = [
            ("Test Draft 1 - Safe to Delete", "First test message"),
            ("Test Draft 2 - Safe to Delete", "Second test message"),
            ("Test Draft 3 - Safe to Delete", "Third test message"),
        ]
        
        try:
            for i, (subject, message) in enumerate(test_messages, 1):
                result = test_imap_settings(
                    self.test_email,
                    subject,
                    f"{message} (Message #{i})"
                )
                self.assertTrue(result, f"Draft {i} creation should succeed")
                
        except Exception as e:
            self.fail(f"Multiple draft creation failed: {e}")

    def test_imap_with_special_characters(self):
        """Test IMAP handling with special characters in content."""
        special_subject = "Test with Special Characters: àáâãäåæçèéêë 中文 🎉"
        special_message = """Test message with special characters:
        - Unicode: àáâãäåæçèéêë
        - Chinese: 你好世界
        - Emoji: 🎉📧✅
        - Symbols: €£¥$"""
        
        result = test_imap_settings(
            self.test_email,
            special_subject,
            special_message
        )
        
        self.assertTrue(result, "IMAP should handle special characters correctly")

    def tearDown(self):
        """Clean up after each test."""
        # Note: We don't automatically delete test emails to allow manual verification
        # Users can manually delete test emails with "Safe to Delete" in the subject
        pass

    @classmethod  
    def tearDownClass(cls):
        """Clean up class-level fixtures."""
        print("\nNote: Test emails with 'Safe to Delete' in subject can be manually removed from Drafts")


if __name__ == '__main__':
    # Print helpful message about online tests
    if not check_imap_config():
        print("IMAP configuration not found at ~/.config/bulkdraft.conf")
        print("Online tests will be skipped. To run them:")
        print("1. Copy bulkdraft.conf.example to ~/.config/bulkdraft.conf")
        print("2. Edit the file with your IMAP settings")
        print("3. Run tests again")
    else:
        print("IMAP configuration found - running online tests")
        print("Note: These tests will create draft emails in your IMAP server")
    
    unittest.main()