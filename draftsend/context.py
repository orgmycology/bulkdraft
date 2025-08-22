"""
Context data loading and processing functionality.
"""

import csv
import os
import yaml


def load_context_file(context_file):
    """
    Load context data from CSV, YAML, or other supported formats.
    
    Args:
        context_file (str): Path to the context data file
        
    Returns:
        list: List of dictionaries containing context data
        
    Raises:
        ValueError: If file format is not supported
    """
    if not context_file or not os.path.exists(context_file):
        return []
    
    ext = os.path.splitext(context_file)[1].lower()
    
    if ext == '.csv':
        with open(context_file, 'r') as file:
            reader = csv.DictReader(file)
            return list(reader)
    elif ext in ['.yml', '.yaml']:
        with open(context_file, 'r') as file:
            data = yaml.safe_load(file)
            if isinstance(data, list):
                return data
            else:
                return [data]
    else:
        raise ValueError(f"Unsupported context file format: {ext}")


def dedupe_records(context_records):
    """
    Remove duplicate email addresses from context records.
    
    Args:
        context_records (list): List of context data dictionaries
        
    Returns:
        list: Deduplicated list of context records
    """
    seen_emails = set()
    deduped_records = []
    for record in context_records:
        email = record.get('email', '').lower().strip()
        if email and email not in seen_emails:
            seen_emails.add(email)
            deduped_records.append(record)
        elif email:
            print(f"Skipping duplicate email: {email} (name: {record.get('first_name', 'unknown')})")
    
    print(f"Processing {len(deduped_records)} unique recipients (removed {len(context_records) - len(deduped_records)} duplicates)")
    return deduped_records