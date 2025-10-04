"""
Utility functions for ML models serialization and data handling
"""

from django.utils import timezone
import json


def serialize_ml_output(data):
    """
    Safely serialize ML output data to JSON-compatible format
    """
    if isinstance(data, dict):
        return {k: serialize_ml_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_ml_output(item) for item in data]
    elif isinstance(data, bool):
        return int(data)  # Convert boolean to 0/1
    elif hasattr(data, 'strftime'):  # datetime objects
        return data.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(data, (int, float, str)) or data is None:
        return data
    else:
        return str(data)  # Fallback to string representation