import hashlib

def generate_file_hash(file_path):
    """
    Generates a SHA-256 hash for a given file.
    This acts as a 'digital fingerprint' for evidence.
    """
    sha256_hash = hashlib.sha256()
    
    # Read the file in chunks to handle large files without crashing your 8GB RAM
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def verify_integrity(file_path, original_hash):
    """
    Compares a file's current hash with its stored hash.
    Used during investigation to prove evidence hasn't been tampered with.
    """
    current_hash = generate_file_hash(file_path)
    return current_hash == original_hash