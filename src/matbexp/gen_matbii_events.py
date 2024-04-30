import argparse
import logging
import sys
from pathlib import Path
from typing import List

from importlib_resources import files

from matbexp import __version__, matbii
from matbexp.matbii.matbii_events import matbii_generate_random_xml
from matbexp.misc.utils import import_dict_from_json

__author__ = "Danielle Benesch"
__copyright__ = "Thales"
__license__ = "Apache-2.0"

_logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 100
VERSION_A = "a"
VERSION_B = "b"
VERSION_C = "c"
CONDITION_HIGH = "high"
CONDITION_LOW = "low"


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from matbexp.skeleton import fib`,
# when using this Python module as a library.


def _get_matbii_params() -> dict:
    parent_path = Path(str(files(matbii)))
    comm_stems_path = Path(parent_path, "matbii_params.json")
    return import_dict_from_json(comm_stems_path)


def generate_and_save_xml(
    seed: int,
    params_dict: dict,
    output_folder: Path,
    condition: str,
    version: str,
    max_attempts: int = MAX_ATTEMPTS,
) -> None:
    """
    Generate and save an XML file based on the provided parameters.

    Args:
        seed (int): Seed for random number generation. This affects the randomness of
            the XML content.
        params_dict (dict): Dictionary of parameters required for XML generation.
        output_folder (Path): Path object representing the directory where the
            generated XML file will be saved.
        condition (str): Condition for the XML file. This affects the number of events.
            Can be ``"high"`` or ``"low"``.
        version (str): Version of the XML file. This is used in the filename of the
            saved XML.
        max_attempts (int, optional): Maximum number of attempts to generate the XML
            file given the default parameters. Defaults to MAX_ATTEMPTS.

    Returns:
        None
    """
    n_task_types = -1
    n_event_times = 0

    attempts = 0
    while n_task_types != n_event_times and attempts < max_attempts:
        # Generate a random XML file
        random_xml, n_task_types, n_event_times = matbii_generate_random_xml(
            random_state=seed, comm_stems_path=None, **params_dict
        )
        seed += 1
        attempts += 1

    if attempts == max_attempts:
        _logger.error("Maximum attempts reached while generating XML.")
        return

    # Save the XML to a file
    output_folder.mkdir(parents=True, exist_ok=True)
    if (condition == CONDITION_LOW) & (version == VERSION_C):
        file_stem = (
            "MATB_EVENTS_tutorial_"
            + str(_get_matbii_params()["MATBII_LOW_PARAMS"]["session_duration_minutes"])
            + "mins"
            + "_seed_"
            + str(seed)
        )
    else:
        file_stem = "MATB_EVENTS_" + condition + "_" + version + "_seed_" + str(seed)
    file_path = output_folder / f"{file_stem}.xml"
    file_path.write_text(random_xml)


def _create_matbii_scenarios(
    condition: str, output_folder: Path, max_attempts: int = MAX_ATTEMPTS
) -> None:
    seed = 0

    params = _get_matbii_params()
    assert "MATBII_HIGH_PARAMS" in params, str(params)
    if condition == CONDITION_HIGH:
        params_dict = params["MATBII_HIGH_PARAMS"]
    elif condition == CONDITION_LOW:
        params_dict = params["MATBII_LOW_PARAMS"]
    else:
        _logger.error(f"Invalid condition: {condition}")
        return

    for version in [VERSION_A, VERSION_B, VERSION_C]:
        if not ((condition == CONDITION_HIGH) & (version == VERSION_C)):
            generate_and_save_xml(
                seed, params_dict, output_folder, condition, version, max_attempts
            )


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line parameters.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"matbexp {__version__}",
    )
    parser.add_argument(
        dest="output_folder", help="Output folder", type=str, metavar="STR"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel: int) -> None:
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args: List[str]) -> None:
    """Wrapper allowing :func:`_create_matbii_scenarios` to be called.
    
    Calls the function with string arguments in a CLI fashion.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    parsed_args = parse_args(args)
    setup_logging(parsed_args.loglevel)
    output_folder = Path(parsed_args.output_folder)
    _create_matbii_scenarios(condition=CONDITION_HIGH, output_folder=output_folder)
    _create_matbii_scenarios(condition=CONDITION_LOW, output_folder=output_folder)

    _logger.info("Script ends here")


def run() -> None:
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
