import os
import glob
import json
from enum import Enum

from seqlbtoolkit.text import substring_mapping

from .macro import CHAR_TO_HTML_LBS, HTML_LBS_TO_CHAR

__all__ = ["get_file_paths", "map_doi_to_filename", "map_filename_to_doi", "StrEnum"]


def get_file_paths(input_dir: str):
    if os.path.isfile(input_dir):
        with open(input_dir, "r", encoding="utf-8") as f:
            file_list = json.load(f)
    elif os.path.isdir(input_dir):
        folder = input_dir
        file_list = list()
        for suffix in ("xml", "html"):
            file_list += glob.glob(os.path.join(folder, f"*.{suffix}"))
    else:
        raise FileNotFoundError("Input file does not exist!")
    return file_list


def map_doi_to_filename(doi):
    name = substring_mapping(doi, CHAR_TO_HTML_LBS)
    return name


def map_filename_to_doi(filename):
    doi = substring_mapping(filename, HTML_LBS_TO_CHAR)
    return doi


class StrEnum(str, Enum):
    @classmethod
    def options(cls):
        opts = list()
        for k, v in cls.__dict__.items():
            if not k.startswith("_") and not isinstance(v, classmethod) and not is_callable(v):
                try:
                    opts.append(v.value)
                except AttributeError:
                    pass
        return opts
