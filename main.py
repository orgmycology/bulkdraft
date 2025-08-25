#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
bulkdraft - A Python utility for creating personalized draft emails.

Main entry point for the bulkdraft application.
"""

from bulkdraft.cli import parse_command_line, process_template_mode
from bulkdraft.imap_client import test_imap_settings


def main():
    """
    Main function - parse command line arguments and dispatch to appropriate handler.
    """
    args = parse_command_line()
    
    if args.command == 'test':
        test_imap_settings(args.email, args.subject, args.message)
    elif args.command == 'template':
        process_template_mode(args)


if __name__ == "__main__":
    main()