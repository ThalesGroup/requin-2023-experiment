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


def get_git_location() -> Path:
    """Find the git location based on the current folder or the location of this file."""
    local_dir = Path().absolute()
    while local_dir != local_dir.parent:
        if (local_dir / ".git").exists():
            return local_dir / ".git"
        local_dir = local_dir.parent

    file_dir = Path(__file__).absolute()
    while file_dir != file_dir.parent:
        if (file_dir / ".git").exists():
            return file_dir / ".git"
        file_dir = file_dir.parent


def get_repo_location() -> Path:
    """Get the path to the current repository.

    Returns:
        Path: The path to the current repository.

    Examples:

    .. ipython:: python

        import sensorhub_modelpipeline as shmp
        shmp.get_repo_location()
    """  # noqa: D412
    return get_git_location().parent
