"""
Configuration management for DraftSend.
"""

import os
import configparser


def load_config():
    """
    Load configuration from ~/.config/draftsend.conf
    
    Returns:
        dict: Configuration settings
        
    Raises:
        SystemExit: If config file is missing or invalid
    """
    config_path = os.path.expanduser('~/.config/draftsend.conf')
    if not os.path.exists(config_path):
        print("❌ Configuration file not found!")
        print(f"Please copy the example configuration file:")
        print(f"  cp draftsend.conf.example ~/.config/draftsend.conf")
        print(f"Then edit ~/.config/draftsend.conf with your IMAP settings.")
        exit(1)
    
    config = configparser.ConfigParser()
    try:
        config.read(config_path)
        return config['DEFAULT']
    except Exception as e:
        print(f"❌ Error reading configuration file: {e}")
        print(f"Please check the format of ~/.config/draftsend.conf")
        exit(1)