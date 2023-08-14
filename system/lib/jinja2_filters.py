import json
import os


def to_json(obj):
    return json.dumps(obj, ensure_ascii=False, indent=4)


def basename(path):
    return os.path.basename(path)


def dirname(path):
    return os.path.dirname(path)
