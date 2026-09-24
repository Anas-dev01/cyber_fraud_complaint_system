from cryptography.fernet import Fernet
import os
from django.conf import settings

# This file will hold the key that locks/unlocks your data
KEY_FILE = os.path.join(settings.BASE_DIR, 'secret.key')

def get_or_create_key():
    """Retrieves the existing key or generates a new one if it doesn't exist."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

def encrypt_data(data):
    """Turns plain text into an encrypted AES-256 string."""
    if not data:
        return None
    key = get_or_create_key()
    f = Fernet(key)
    # Convert string to bytes, encrypt, then back to string for database storage
    return f.encrypt(data.encode()).decode()

def decrypt_data(token):
    """Turns an encrypted string back into readable plain text."""
    if not token:
        return None
    key = get_or_create_key()
    f = Fernet(key)
    try:
        return f.decrypt(token.encode()).decode()
    except Exception:
        # If decryption fails (e.g. wrong key), return a warning
        return "Decryption Error"