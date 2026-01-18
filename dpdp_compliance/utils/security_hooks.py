import frappe
from dpdp_compliance.utils.encryption import encrypt_data, decrypt_data

# List of (DocType, Field) to encrypt
ENCYPTED_FIELDS = {
    "Data Subject Request": ["description"],
    # Add more as needed, e.g. ("User", "phone") - careful with core datatypes
}


def encrypt_fields(doc, method):
    """
    Encrypts configured fields before saving to the database.
    """
    if doc.doctype not in ENCYPTED_FIELDS:
        return

    fields_to_encrypt = ENCYPTED_FIELDS[doc.doctype]
    for field in fields_to_encrypt:
        val = doc.get(field)
        if val and not val.startswith(
            "gAAAA"
        ):  # Simple check to avoid double encryption if logic flakiness
            # Encrypt
            encrypted = encrypt_data(val)
            doc.set(field, encrypted)


def decrypt_fields(doc, method):
    """
    Decrypts configured fields on document load.
    """
    if doc.doctype not in ENCYPTED_FIELDS:
        return

    fields_to_decrypt = ENCYPTED_FIELDS[doc.doctype]
    for field in fields_to_decrypt:
        val = doc.get(field)
        if val and str(val).startswith(
            "gAAAA"
        ):  # Fernet tokens usually start with gAAAA
            # Decrypt
            decrypted = decrypt_data(val)
            doc.set(field, decrypted)
