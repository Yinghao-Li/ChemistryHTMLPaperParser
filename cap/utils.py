import os
import glob
import json


def get_file_paths(input_dir: str):
    if os.path.isfile(input_dir):
        with open(input_dir, 'r', encoding='utf-8') as f:
            file_list = json.load(f)
    elif os.path.isdir(input_dir):
        folder = input_dir
        file_list = list()
        for suffix in ('xml', 'html'):
            file_list += glob.glob(os.path.join(folder, f"*.{suffix}"))
    else:
        raise FileNotFoundError("Input file does not exist!")
    return file_list
