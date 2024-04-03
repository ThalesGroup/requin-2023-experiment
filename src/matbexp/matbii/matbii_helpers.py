import xml.dom.minidom  # noqa S408
from pathlib import Path
from typing import Optional
from xml.etree.ElementTree import Element  # noqa S405

import numpy as np
from importlib_resources import files

from matbexp import matbii

from ..misc.utils import import_dict_from_json


def _format_seconds(seconds: int) -> str:
    """
    Converts the total number of seconds into a string representation
    in the format "HH:MM:SS".

    Args:
        seconds (int): The total number of seconds.

    Returns:
        str: The formatted time string.
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _parse_time_string(time_string: str) -> int:
    """
    Parses a time string in the format "HH:MM:SS" and returns the total number of
    seconds.

    Args:
        time_string (str): The time string in the format "HH:MM:SS".

    Returns:
        int: The total number of seconds.

    Raises:
        ValueError: If the time string is in an invalid format.
    """
    try:
        hours, minutes, seconds = map(int, time_string.split(":"))
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        return total_seconds
    except ValueError as e:
        # Handle invalid time string format
        raise ValueError("Invalid time string format. Expected format: HH:MM:SS") from e


def _has_repeated_values(array: np.ndarray, max_repeats: int, window_size: int) -> bool:
    """Check if an array has repeated values within a sliding window.

    Args:
        array (np.ndarray): The input array to check for repeated values.
        max_repeats (int): The maximum number of allowed repeated values within the
            window.
        window_size (int): The size of the sliding window.

    Returns:
        bool: True if the array has repeated values within the window, False otherwise.
    """
    for i in range(len(array) - window_size + 1):
        window = array[i : i + window_size]
        _, counts = np.unique(window, return_counts=True)
        if np.max(counts) > max_repeats:
            return True
    return False


def _remove_one_level_indent(txt: str, max_indent: int = 10) -> str:
    """Remove one level of indentation for each line in the text.

    Args:
        txt (str): The input text with indentation.
        max_indent (int): The maximum number of indentation levels to consider.
            Default is 10.

    Returns:
        str: The modified text with one level of indentation removed from each line.
    """
    lines = txt.split("\n")
    for i in range(len(lines)):
        indent_removed = False
        for j in list(reversed(list(np.arange(max_indent)))):
            original_indent = r"".join(["\t"] * (j + 1))
            new_indent = r"".join(["\t"] * j)
            if original_indent in lines[i] and not indent_removed:
                lines[i] = lines[i].replace(original_indent, new_indent)
                indent_removed = True

    modified_txt = "\n".join(lines)
    return modified_txt


def _remove_blank_lines(txt: str) -> str:
    """Remove blank lines from the given text.

    Args:
        txt (str): The input text.

    Returns:
        str: The text with blank lines removed.
    """
    lines = txt.splitlines()
    non_blank_lines = [line for line in lines if line.strip()]
    return "\n".join(non_blank_lines)


def _pretty_format_xml(xml_string: str, xml_declaration: Optional[str] = None) -> str:
    # Pretty print the XML with tab indentations
    dom = xml.dom.minidom.parseString(xml_string)  # noqa S318
    pretty_xml = dom.toprettyxml(indent="\t")

    if xml_declaration is not None:
        current_declaration = pretty_xml.split("\n")[0]
        pretty_xml = pretty_xml.replace(current_declaration, xml_declaration)

    modified_xml = _remove_one_level_indent(pretty_xml)
    final_xml = _remove_blank_lines(modified_xml)
    return final_xml


def _get_matbii_comm_stems() -> dict:
    parent_path = Path(str(files(matbii)))
    comm_stems_path = Path(parent_path, "matbii_comm_stems.json")
    return import_dict_from_json(comm_stems_path)


def _get_seconds_from_elem(elem: Element) -> int:
    return _parse_time_string(elem.attrib["startTime"])


def _sort_events_by_seconds(root: Element) -> Element:
    """Sort events by startTime"""
    root[:] = sorted(root, key=_get_seconds_from_elem)
    return root
