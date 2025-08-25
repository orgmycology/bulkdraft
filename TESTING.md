# bulkdraft Testing Guide

This document describes how to run and understand the bulkdraft test suite.

## Test Suite Overview

The bulkdraft test suite is comprehensive and includes both offline and online tests:

- **Offline Tests**: Test function logic and responses without requiring IMAP connections
- **Online Tests**: Test IMAP integration by creating actual draft emails (requires configuration)

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_config.py             # Configuration loading tests
├── test_template.py           # Template processing tests  
├── test_context.py            # Context data processing tests
├── test_email_builder.py      # Email building and formatting tests
├── test_calendar.py           # ICS calendar creation tests
├── test_imap_offline.py       # IMAP functionality tests (mocked)
├── test_imap_online.py        # IMAP integration tests (live)
└── test_cli.py                # Command line interface tests
```

## Running Tests

### Quick Start

```bash
# Run all tests (offline + online)
python run_tests.py

# Run only offline tests (no IMAP required)
python run_tests.py --mode offline

# Run only online tests (requires IMAP config)
python run_tests.py --mode online
```

### Advanced Usage

```bash
# Run specific test module
python run_tests.py --module test_config

# Run with verbose output
python run_tests.py --verbose

# Run using standard unittest
python -m unittest discover tests/ -v
```

## Test Categories

### Offline Tests

These tests run without any external dependencies and test the core functionality:

#### Configuration Tests (`test_config.py`)
- ✅ Configuration file loading and validation
- ✅ Error handling for missing/invalid config files
- ✅ Helpful error messages and guidance

#### Template Tests (`test_template.py`)
- ✅ YAML front matter parsing
- ✅ Jinja2 template rendering with defaults
- ✅ Context data integration
- ✅ Metadata template rendering with dependency handling
- ✅ Error handling for invalid templates

#### Context Tests (`test_context.py`)
- ✅ CSV file loading and parsing
- ✅ YAML file loading (list and single object formats)
- ✅ Email deduplication (case-insensitive)
- ✅ Include/exclude filtering
- ✅ Error handling for unsupported formats

#### Email Builder Tests (`test_email_builder.py`)
- ✅ HTML wrapping with email-compatible CSS
- ✅ HTML to plain text conversion
- ✅ MIME message structure creation
- ✅ Calendar attachment handling
- ✅ Email headers and metadata

#### Calendar Tests (`test_calendar.py`)
- ✅ ICS file generation from metadata
- ✅ Timezone handling and validation
- ✅ Date format parsing and error handling
- ✅ Template variable resolution

#### IMAP Offline Tests (`test_imap_offline.py`)
- ✅ Drafts folder detection logic
- ✅ Draft saving with proper flags
- ✅ Connection error handling
- ✅ Authentication failure handling

#### CLI Tests (`test_cli.py`)
- ✅ Command line argument parsing
- ✅ Template processing workflow
- ✅ Include/exclude filtering
- ✅ Backward compatibility

### Online Tests

These tests require actual IMAP server access and create real draft emails:

#### IMAP Online Tests (`test_imap_online.py`)
- 🌐 Real IMAP connection and authentication
- 🌐 Draft creation in actual IMAP server
- 🌐 Drafts folder detection on live server
- 🌐 Multiple draft creation workflow
- 🌐 Special character handling
- 🌐 Integration testing with full email pipeline

**Note**: Online tests will be skipped if IMAP configuration is not available.

## Test Configuration

### For Offline Tests
No configuration required - all dependencies are mocked.

### For Online Tests
1. Copy configuration template:
   ```bash
   cp bulkdraft.conf.example ~/.config/bulkdraft.conf
   ```

2. Edit `~/.config/bulkdraft.conf` with your IMAP settings:
   ```ini
   [DEFAULT]
   imap_server=your.imap.server
   imap_port=993
   imap_username=your-username
   imap_password=your-password  
   from_email=your-email@domain.com
   ```

3. Run online tests:
   ```bash
   python run_tests.py --mode online
   ```

## Test Output

### Successful Run
```
test_config_loading (tests.test_config.TestConfig) ... ok
test_template_rendering (tests.test_template.TestTemplate) ... ok
test_email_deduplication (tests.test_context.TestContext) ... ok
...

----------------------------------------------------------------------
Ran 45 tests in 2.341s

OK
```

### With Failures
```
test_invalid_template (tests.test_template.TestTemplate) ... FAIL

======================================================================
FAIL: test_invalid_template (tests.test_template.TestTemplate)
----------------------------------------------------------------------
AssertionError: Template should handle invalid syntax gracefully
...
```

## Understanding Test Results

### Online Test Behavior
- Online tests create actual draft emails with subjects containing "Safe to Delete"
- These drafts can be manually removed from your IMAP server
- Tests verify drafts are created with proper flags for editability
- Failed online tests usually indicate IMAP configuration issues

### Test Coverage Areas

| Component | Offline Tests | Online Tests | Coverage |
|-----------|---------------|--------------|----------|
| Configuration | ✅ | ✅ | Full |
| Template Processing | ✅ | ➖ | Complete |
| Context Data | ✅ | ➖ | Complete |
| Email Building | ✅ | ✅ | Full |
| Calendar Creation | ✅ | ✅ | Full |
| IMAP Integration | ✅ (mocked) | ✅ (live) | Full |
| CLI Interface | ✅ | ➖ | Complete |

## Troubleshooting Tests

### Common Issues

1. **Import Errors**
   ```bash
   ModuleNotFoundError: No module named 'bulkdraft'
   ```
   - Ensure you're running tests from the project root directory
   - Check that `__init__.py` files exist in all package directories

2. **Online Tests Skipped**
   ```
   IMAP configuration not found - skipping online tests
   ```
   - Copy and configure `~/.config/bulkdraft.conf`
   - Verify IMAP credentials are correct

3. **IMAP Connection Failures**
   ```
   IMAP test failed: [Errno 61] Connection refused
   ```
   - Check IMAP server settings and port
   - Verify network connectivity
   - Ensure IMAP is enabled on email provider

4. **Authentication Errors**
   ```
   IMAP test failed: Authentication failed
   ```
   - Verify username and password
   - For Gmail: Use App Password, not regular password
   - Enable IMAP access in email settings

### Test Data Cleanup

Online tests create draft emails that can be manually deleted:
- Look for subjects containing "bulkdraft Test" or "Safe to Delete"  
- These are safe to remove from your Drafts folder
- Tests do not automatically clean up to allow manual verification

## Contributing Tests

When adding new functionality:

1. **Add Offline Tests**: Test the core logic with mocked dependencies
2. **Add Online Tests**: Test integration with real IMAP servers when applicable
3. **Update Documentation**: Document new test modules and their purpose
4. **Maintain Coverage**: Ensure new code has appropriate test coverage

### Test Writing Guidelines

- Use descriptive test method names: `test_template_rendering_with_context`
- Include docstrings explaining what each test verifies
- Mock external dependencies in offline tests
- Use setup/teardown methods for common test fixtures
- Test both success and failure cases
- Include edge cases and error conditions

## Performance Considerations

- Offline tests should run quickly (< 5 seconds total)
- Online tests may take longer due to network operations
- Tests run in parallel where possible
- Use `@unittest.skip()` for tests that require special conditions

## Continuous Integration

The test suite is designed to work in CI environments:
- Offline tests run without any configuration
- Online tests are automatically skipped without IMAP config
- Exit codes indicate success (0) or failure (1)
- Verbose output available for debugging