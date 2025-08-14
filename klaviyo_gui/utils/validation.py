"""
Simple input validation utilities
"""

def validate_api_key(api_key: str) -> bool:
    """Basic API key validation"""
    return bool(api_key and api_key.strip() and len(api_key.strip()) > 10)

def validate_segment_id(segment_id: str) -> bool:
    """Basic segment ID validation"""
    return bool(segment_id and segment_id.strip())

def validate_event_name(event_name: str) -> bool:
    """Basic event name validation"""
    return bool(event_name and event_name.strip())