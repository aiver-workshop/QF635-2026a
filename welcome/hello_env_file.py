"""
You should NEVER hardcode any sensitive information such as password in Python script.
A safer way to handle credential is saving them in a local file and load as environment variables.
There are more secure ways to manage secrets such as using Secret Manager service by cloud providers.
Students are encourage to explore further.

Use Notepad to create a "secrets.txt" file under home directory ~/vault to store <key>=<value> pairs, for example:
key=abc
secret=123

Note: If your computer is compromised, then potentially your secret files are exposed too.
"""

import os
from dotenv import load_dotenv

# 1. Define the path to your secret vault
# Using '.env' is the industry standard naming convention
env_path = os.path.expanduser('~/vault/secrets.txt')

# 2. Load the variables from the file into the system environment
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    print(f"Warning: Configuration file not found at {env_path}")

# 3. Retrieve the variables using os.getenv
# We use a default value (None) to handle cases where the key is missing
my_username = os.getenv('key')
my_password = os.getenv('secret')

# 4. Verification (In a real app, don't print passwords!)
if my_username and my_password:
    print(f"Successfully loaded credentials for: {my_username}")
    print(f"Secret: {my_password}")
else:
    print("Error: Could not find 'key' or 'secret' in the environment.")

