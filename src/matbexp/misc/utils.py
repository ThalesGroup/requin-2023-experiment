import json
from collections import OrderedDict
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Union


def import_dict_from_json(import_path: Union[str, Path]) -> dict:
    """Export a dictionary to a JSON file.

    Args:
        import_path (Union[str, Path]): The path to the json file.
            Should end in ``.json``.

    Returns:
        dict: The contents of the imported JSON file.
    """
    with open(import_path) as f:
        data = f.read()
    try:
        data_dict = json.loads(data, object_pairs_hook=OrderedDict)
    except JSONDecodeError:
        data_dict = data
    if isinstance(data_dict, dict):
        return data_dict
    else:
        return {"data": data}
