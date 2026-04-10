"""Shared utility functions"""

def mask_secret(value: str | None, keep_start: int = 3, keep_end: int = 4) -> str:
    """Mask sensitive secret with asterisks, keeping a few characters for user recognition"""
    if not value:
        return ""
    if len(value) <= keep_start + keep_end:
        return "*" * len(value)
    return value[:keep_start] + "*" * (len(value) - keep_start - keep_end) + value[-keep_end:]
