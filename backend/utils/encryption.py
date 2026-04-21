"""
Utility for encrypting/decrypting OAuth tokens before storing in database
Ensures secure storage of sensitive access tokens
"""

from cryptography.fernet import Fernet
import os
import base64

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# If not set, generate one (for development only - MUST set in production)
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"\n⚠️  ===== ENCRYPTION KEY NOT SET =====")
    print(f"⚠️  Generated temporary key: {ENCRYPTION_KEY}")
    print(f"⚠️  Add this to your .env file as ENCRYPTION_KEY")
    print(f"⚠️  ====================================\n")

cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

def encrypt_token(token: str) -> str:
    """
    Encrypt an OAuth token for secure storage in database
    
    Args:
        token: Plain text token to encrypt
        
    Returns:
        Base64-encoded encrypted token
    """
    if not token:
        return None
    
    try:
        encrypted = cipher_suite.encrypt(token.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        print(f"❌ Token encryption failed: {e}")
        return None

def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt an OAuth token for use in API calls
    
    Args:
        encrypted_token: Base64-encoded encrypted token from database
        
    Returns:
        Plain text token
    """
    if not encrypted_token:
        return None
    
    try:
        decoded = base64.b64decode(encrypted_token.encode())
        decrypted = cipher_suite.decrypt(decoded)
        return decrypted.decode()
    except Exception as e:
        print(f"❌ Token decryption failed: {e}")
        return None

def generate_key():
    """Generate a new encryption key (use once during setup)"""
    return Fernet.generate_key().decode()

if __name__ == "__main__":
    # Test encryption/decryption
    print("\n🔐 Testing encryption utility...")
    test_token = "test_access_token_12345"
    encrypted = encrypt_token(test_token)
    decrypted = decrypt_token(encrypted)
    
    print(f"Original:  {test_token}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {'✅' if test_token == decrypted else '❌'}\n")
