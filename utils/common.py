import os
from pathlib import Path
from utils import global_const as gc
import re


def get_project_root():
    # Returns project root folder.
    return Path(__file__).parent.parent


def file_exists(fn):
    try:
        with open(fn, "r"):
            return 1
    except IOError:
        return 0


def is_excel(file_path):
    ext = Path(file_path).suffix
    if 'xls' in ext:
        return True
    else:
        return False

