"""
TOPIC: Secure Credential Management using Environment Variables
REFERENCE: https://pypi.org

ACTUAL FOLDER LOCATIONS:
- Windows: C:\\Users\\<YourUsername>\\vault\\secret_file
- macOS:   //Users//<YourUsername>//vault//secret_file

KEY TEACHING POINTS:
1. Path Abstraction: Using 'os.path.expanduser' allows the same code to run
   on any OS by resolving the '~' symbol to the correct home folder.
2. Permission Safety: By storing keys in the user's home directory, we
   leverage OS-level permissions to keep other users out of our secrets.
3. Git Safety: By keeping the 'vault' folder outside of our 'GitHub' or
   project folders, we eliminate the risk of accidental key leaks.

NOTE:
Secret file content looks as follows:
    API_KEY=abc
    API_SECRET=123
"""

import os
from dotenv import load_dotenv

# Check location of home directory
print(os.path.expanduser("~"))

# location of secret file under home directory
dotenv_path = '~/vault/secret_file'
dotenv_path = os.path.expanduser('~/vault/secret_file.txt')

# read secret
load_dotenv(dotenv_path=dotenv_path)
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

# Security check to ensure the variables are not empty
if API_KEY and API_SECRET:
    print(f"Credentials verified for key starting with: {API_KEY[:5]}")
else:
    print("Failed to retrieve environment variables. Check file formatting.")