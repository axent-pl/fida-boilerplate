import hashlib
import base64

def urlsafe_hash(string_list, hash_length=16):
    combined_string = '/'.join(string_list)
    hash_object = hashlib.sha256(combined_string.encode())
    hash_digest = hash_object.digest()
    base64_encoded = base64.urlsafe_b64encode(hash_digest).decode()
    return base64_encoded[:hash_length]