"""
Calendar (ICS) file creation functionality.
"""

import pytz
from datetime import datetime
from ics import Calendar, Event


def create_ics_file(metadata):
    """
    Create ICS calendar file from event metadata.
    
    Args:
        metadata (dict): Event metadata containing event details
        
    Returns:
        str: Serialized ICS calendar content
    """
    cal = Calendar()
    event = Event()
    event.name = metadata.get('event_name', 'Event')
    
    # Parse the date and apply the timezone
    timezone_str = metadata.get('timezone', 'UTC')
    event_date_str = metadata.get('event_date', '2023-12-01 10:00:00')
    
    # Debug: Check if timezone is properly rendered
    if timezone_str.startswith('{{') and timezone_str.endswith('}}'):
        print(f"Warning: Timezone not properly rendered: {timezone_str}")
        timezone_str = 'UTC'  # Fallback to UTC
    
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        print(f"Warning: Unknown timezone '{timezone_str}', falling back to UTC")
        local_tz = pytz.timezone('UTC')
    
    try:
        naive_datetime = datetime.strptime(event_date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print(f"Warning: Invalid date format '{event_date_str}', using current time")
        naive_datetime = datetime.now()
    
    local_datetime = local_tz.localize(naive_datetime)
    
    event.begin = local_datetime
    event.location = metadata.get('event_location', 'TBD')
    cal.events.add(event)
    return cal.serialize()