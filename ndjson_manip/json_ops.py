# Copyright 2026 by Hans Meine, licensed under the Apache License 2.0
"""Helper functions for JSON manipulation using dot notation for keys."""


def lookup_key(obj, key: str):
    """Check if the object has the given key."""
    if not key:
        return obj
    if not isinstance(obj, dict):
        raise KeyError
    head, tail = key.split(".", 1) if "." in key else (key, "")
    value = obj[head]
    return lookup_key(value, tail)


def set_key(obj: dict, key: str, value):
    """Set the value of the given key in the object."""
    assert key
    assert isinstance(obj, dict)

    if "." in key:
        head, tail = key.split(".", 1)
        set_key(obj[head], tail, value)
    else:
        obj[key] = value
