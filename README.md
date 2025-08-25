# bulkdraft

A Python utility for creating personalized draft emails with calendar invitations from templates and context data. Perfect for bulk invitations, newsletters, or any personalized email campaigns.

## Features

- 📧 **Template-based emails** with Jinja2 templating
- 📊 **Context data support** from CSV or YAML files
- 📅 **Calendar invitations** (ICS files) automatically generated
- 🔧 **IMAP integration** to save drafts directly to your email client
- ✅ **Test mode** for validating IMAP settings
- 🔄 **Backward compatibility** with existing workflows
- 🚫 **Email deduplication** prevents multiple emails to same recipient
- ✔️ **Include/exclude filtering** with boolean column support
- 📱 **Multi-client compatibility** with proper HTML and plain text formats

## Installation

### Dependencies

Install the required Python packages:

```bash
pip install pyyaml~=6.0 markdown~=3.4 ics~=0.7 pytz~=2023.3 jinja2~=3.1
```

### Configuration

1. Copy the configuration template:
   ```bash
   cp bulkdraft.conf.example ~/.config/bulkdraft.conf
   ```

2. Edit `~/.config/bulkdraft.conf` with your IMAP settings:
   ```ini
   [DEFAULT]
   imap_server=imap.gmail.com
   imap_port=993
   imap_username=your-email@gmail.com
   imap_password=your-app-password
   from_email=your-email@gmail.com
   ```

   **Note:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

3. **If the configuration file is missing**, the tool will show a helpful error message:
   ```
   ❌ Configuration file not found!
   Please copy the example configuration file:
     cp bulkdraft.conf.example ~/.config/bulkdraft.conf
   Then edit ~/.config/bulkdraft.conf with your IMAP settings.
   ```

## Usage

bulkdraft has two main modes: **template processing** and **IMAP testing**.

### Test IMAP Settings

Before processing templates, test your IMAP configuration:

```bash
python main.py test "recipient@example.com" "Test Subject" "Test message content"
```

This will create a single draft email to verify your IMAP settings are working.

### Template Processing

#### Basic Usage

```bash
# Process template with CSV context data
python main.py template example.txt --context recipients.csv

# Or using the legacy format (backward compatible)  
python main.py example.txt --context recipients.csv
```

#### Template File Format

Templates use YAML front matter for metadata and Jinja2 templating for dynamic content:

```markdown
---
event_name: "{{ event_name | default('Team Meeting') }}"
event_date: "{{ event_date | default('2023-12-15 10:00:00') }}"
event_location: "{{ event_location | default('Conference Room') }}"
timezone: "{{ timezone | default('America/New_York') }}"
subject: "{{ subject | default('Invitation: ' + event_name) }}"
---

Dear {{ first_name | default('Team Member') }},

You're invited to **{{ event_name }}** on {{ event_date }}.

**Event Details:**
- Date: {{ event_date }}
- Location: {{ event_location }}
- Timezone: {{ timezone }}

Best regards,
The Event Team

---
*This email was sent to {{ email }}*
```

#### Context Data Files

##### CSV Format

```csv
first_name,last_name,email,event_name,include
John,Doe,john@example.com,Project Kickoff,TRUE
Jane,Smith,jane@example.com,Project Kickoff,FALSE
Alice,Johnson,alice@example.com,Project Kickoff,TRUE
```

**Note:** The optional `include` column allows you to control which rows are processed. Only rows with `include` set to `TRUE` (case-insensitive) will have emails generated. Rows with `FALSE`, empty values, or any other text will be skipped.

**Email Deduplication:** The tool automatically removes duplicate email addresses (case-insensitive) to prevent multiple invitations to the same person. It shows which duplicates are skipped and provides a summary of unique recipients.

##### YAML Format

```yaml
- first_name: John
  last_name: Doe
  email: john@example.com
  event_name: Project Kickoff
- first_name: Jane
  last_name: Smith
  email: jane@example.com
  event_name: Project Kickoff
```

### Advanced Features

#### Template Variables

Templates support Jinja2 syntax with the following available variables:

- **From YAML metadata**: `event_name`, `event_date`, `event_location`, `timezone`, `subject`
- **From context data**: Any columns from your CSV/YAML file (e.g., `first_name`, `last_name`, `email`)
- **Filters**: Use Jinja2 filters like `{{ variable | default('fallback') }}`
- **Conditionals**: `{% if variable %}...{% endif %}`

#### Email Format Support

- **HTML emails** with proper structure and CSS styling
- **Plain text fallback** for accessibility and older clients  
- **Calendar invitations** (ICS files) with both attachment and inline formats
- **Mobile-responsive** design for email clients

#### Calendar Integration

The tool automatically creates ICS calendar files based on the metadata:
- Uses `event_name` for the calendar event title
- Uses `event_date` (format: `YYYY-MM-DD HH:MM:SS`) for scheduling
- Uses `event_location` for the event location
- Uses `timezone` for proper timezone handling
- **Dual format**: Both attachment and inline for maximum email client compatibility

#### Quality Control Features

- **Email deduplication**: Prevents multiple emails to the same address
- **Include/exclude filtering**: Boolean column support for selective sending
- **Template validation**: Error handling for invalid templates
- **IMAP draft flags**: Proper draft creation for editability in email clients

## Command Reference

### Template Mode

```bash
python main.py template <template_file> [--context <data_file>]
python main.py <template_file> [--context <data_file>]  # Legacy format
```

**Arguments:**
- `template_file`: Path to your email template file
- `--context`: Path to CSV or YAML file with context data
- `--csv`: (Deprecated) Use `--context` instead

### Test Mode

```bash
python main.py test <email> <subject> <message>
```

**Arguments:**
- `email`: Recipient email address
- `subject`: Email subject line
- `message`: Email message content

## Examples

### Simple Event Invitation

1. Create `invitation.txt`:
   ```markdown
   ---
   event_name: "Weekly Team Sync"
   event_date: "2023-12-15 10:00:00"
   event_location: "Zoom Meeting Room"
   timezone: "America/New_York"
   ---

   Hi {{ first_name }},

   Join us for our {{ event_name }} on {{ event_date }}.
   ```

2. Create `team.csv`:
   ```csv
   first_name,email
   Alice,alice@company.com
   Bob,bob@company.com
   ```

3. Run:
   ```bash
   python main.py template invitation.txt --context team.csv
   ```

### Testing Configuration

```bash
python main.py test "test@example.com" "Configuration Test" "Testing IMAP setup"
```

## Troubleshooting

### Common Issues

1. **Configuration File Missing**
   ```
   ❌ Configuration file not found!
   ```
   - Copy `bulkdraft.conf.example` to `~/.config/bulkdraft.conf`
   - Edit with your IMAP settings

2. **Authentication Failed**
   - For Gmail: Use App Passwords, not your regular password
   - Enable 2-factor authentication first, then generate an App Password

3. **Connection Timeout**
   - Verify `imap_server` and `imap_port` settings
   - Check firewall/network restrictions

4. **Drafts Not Editable**
   - Tool now sets proper `\\Draft` flags for editability
   - Check that drafts folder is correctly detected

5. **Template Errors**
   - Ensure YAML front matter is properly formatted with `---` separators
   - Check Jinja2 template syntax
   - Avoid circular references in template variables

6. **Missing Context Variables**
   - Use `{{ variable | default('fallback') }}` for optional variables
   - Verify CSV/YAML column names match template variables

7. **Duplicate Emails**
   - Tool automatically deduplicates by email address
   - Check output for "Skipping duplicate email" messages

### Debug Mode

Add error handling by running with Python's verbose mode:
```bash
python -v main.py test "email@example.com" "Test" "Message"
```

## Development and Testing

bulkdraft includes a comprehensive test suite with both offline and online tests.

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run only offline tests (no IMAP required)
python run_tests.py --mode offline

# Run only online tests (requires IMAP config)  
python run_tests.py --mode online

# Run specific test module
python run_tests.py --module test_config
```

### Project Structure

```
bulkdraft/
├── main.py                    # Main entry point
├── bulkdraft/                 # Package modules
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── template.py            # Template processing
│   ├── context.py             # Context data handling
│   ├── email_builder.py       # Email construction
│   ├── calendar.py            # ICS calendar creation
│   ├── imap_client.py         # IMAP operations
│   └── cli.py                 # Command line interface
├── tests/                     # Test suite
│   ├── test_*.py              # Individual test modules
│   └── test_imap_online.py    # Online integration tests
├── run_tests.py               # Test runner
├── TESTING.md                 # Testing documentation
├── example.txt                # Example template
├── recipients.csv             # Example context data
└── bulkdraft.conf.example     # Configuration template
```

For detailed testing information, see [TESTING.md](TESTING.md).

## Email Provider Setup

### Gmail
- Server: `imap.gmail.com:993`
- Enable 2FA and create an App Password
- Use App Password in configuration

### Outlook/Office 365
- Server: `outlook.office365.com:993`
- May require app-specific authentication

### Yahoo Mail
- Server: `imap.mail.yahoo.com:993`
- Enable "Allow apps that use less secure sign in"

### Custom/Corporate
- Contact your IT administrator for IMAP settings
- Typically port 993 (SSL) or 143 (non-SSL)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.