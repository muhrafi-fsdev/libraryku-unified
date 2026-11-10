"""Validasi ID MongoDB tanpa bergantung pada pymongo (mudah diuji)."""
import re

_OBJECT_ID = re.compile(r"[0-9a-fA-F]{24}")


def is_valid_object_id(value):
    """True hanya untuk string tepat 24 karakter heksadesimal (bentuk ObjectId)."""
    return isinstance(value, str) and _OBJECT_ID.fullmatch(value) is not None
