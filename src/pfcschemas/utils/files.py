import os
from json import load


def validate_json(file: dict|str|os.PathLike) -> dict:
    if isinstance(file, dict):
        return file
    elif isinstance(file, str) or isinstance(file, os.PathLike):
        with open(file, 'r') as f:
            return load(f)
    else:
        raise ValueError("expected a dict, str or os.PathLike")
    
