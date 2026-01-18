
import frappe
from cryptography.fernet import Fernet
from frappe.utils import get_site_path
import os

def get_encryption_key():
	"""
	Retrieves the encryption key from site_config.json.
	If not present, looks for 'encryption_key' in frappe.conf.
	"""
	key = frappe.conf.get("encryption_key")
	if not key:
		# Fallback or Error? Ideally strict.
		# For development, we might generate one? No, strict is better for compliance.
		frappe.throw("Encryption Key not found in site_config.json. Please set 'encryption_key' using `bench set-config encryption_key <key>`")
	return key

def encrypt_data(data):
	"""
	Encrypts plaintext data using Fernet (symmetric encryption).
	"""
	if not data:
		return data
		
	key = get_encryption_key()
	f = Fernet(key)
	
	if isinstance(data, str):
		data = data.encode('utf-8')
		
	encrypted = f.encrypt(data)
	return encrypted.decode('utf-8') # Return as string for database storage

def decrypt_data(encrypted_data):
	"""
	Decrypts ciphertext back to plaintext.
	"""
	if not encrypted_data:
		return encrypted_data
		
	key = get_encryption_key()
	f = Fernet(key)
	
	try:
		if isinstance(encrypted_data, str):
			encrypted_data = encrypted_data.encode('utf-8')
			
		decrypted = f.decrypt(encrypted_data)
		return decrypted.decode('utf-8')
	except Exception:
		# If decryption fails (e.g., data was not encrypted), return original?
		# Or throw error? For migration safety, sometimes returning original is safer 
		# IF we assume mixed data. But strictly, it should fail if expected encrypted.
		# Let's log and return original for resilience during dev, but warn.
		frappe.log_error("Decryption failed", "DPDP Encryption Error")
		return str(encrypted_data)
