import random
import re
from typing import Optional, Tuple
from xml.etree.ElementTree import Element, SubElement

from matbexp.matbii.matbii_events import (
    _adjust_task_types,
    _finalize_matbii_generation,
    _generate_auto_and_comm_start_stop,
    _generate_event_times_and_task_types,
    _generate_tasks,
    _get_comm_stems,
    _initialize_matbii_generation,
)
from matbexp.matbii.matbii_helpers import _format_seconds, _parse_time_string


def matbii_generate_random_xml_with_text_file(
    text_file: str,
    random_state: Optional[int] = None,
    min_seconds_event_diff: int = 10,
    max_seconds_event_diff: int = 35,
    session_duration_minutes: int = 10,
    min_seconds_fail_fix_resman: int = 20,
    max_seconds_fail_fix_resman: int = 90,
    min_seconds_to_indicate_no_comm: int = 90,
    seconds_before_comm_stop: int = 30,
    seconds_after_comm_start: int = 5,
    n_pump_failures: int = 5,
    n_own_comm: int = 5,
    n_other_comm: int = 5,
    n_green_red_issues: int = 6,
    n_systems_up_down: int = 6,
    total_auto_minutes: int = 3,
    comm_stems_path: Optional[str] = None,
) -> Tuple[str, int, int]:
    """Generate a random XML file.

    Args:
        random_state (Optional[int]): Random seed for the random number generator. If
            provided, it ensures reproducibility by setting the seed. Default is
            ``None``, which results in non-reproducible random numbers.
        min_seconds_event_diff (int): The minimum time difference between events in
            seconds. Default is 10.
        max_seconds_event_diff (int): The maximum time difference between events in
            seconds. Default is 35.
        session_duration_minutes (int): The duration of the session in minutes.
            Default is 10.
        min_seconds_fail_fix_resman (int): The minimum time difference between the fail
            and fix tasks in the Resource Management event.
            Default is 20.
        max_seconds_fail_fix_resman (int): The maximum time difference between the fail
            and fix tasks in the Resource Management event.
            Default is 90.
        min_seconds_to_indicate_no_comm (int): The minimum time difference required
            between two communication tasks to indicate to the participant that there is
            no communication for this interval. Default is 90.
        seconds_before_comm_stop (int): How many seconds should be before the
            indication of stopping communication, following the last communication task
            in a long interval. This should also be the minimum time difference between
            the last communication task and the end of the experiment. Default is 30.
        seconds_after_comm_start (int): How many seconds after the indication of
            starting communication that the first communication in a long interval
            should start. Default is 5.
        n_pump_failures (int): The number of pump failures. Default is 5.
        n_own_comm (int): The number of own communications tasks. Default is 5.
        n_other_comm (int): The number of other communications tasks. Default is 5.
        n_green_red_issues (int): The number of green/red system monitoring tasks.
            Default is 6.
        n_systems_up_down (int): The number of systems up/down system monitoring tasks.
            Default is 6.
        total_auto_minutes (int): The number of minutes for the auto task. Default is 3.
        comm_stems_path (Optional[str]): The path to the parent folder containing
            communications audio files. Default is ``None``. If ``None``, will use a
            pre-existing list of communications audio files.

    Returns:
        Tuple[str, int, int]: A tuple containing the generated XML string,
            the number of task types, and the number of event times.
    """
    xml_declaration, root, comm_stems_per_ship = _initialize_matbii_generation(
        random_state=random_state, comm_stems_path=comm_stems_path
    )
    (
        session_duration_seconds,
        event_times,
        task_types,
    ) = _generate_event_times_and_task_types(
        session_duration_minutes,
        min_seconds_event_diff,
        max_seconds_event_diff,
        n_pump_failures,
        n_own_comm,
        n_other_comm,
        n_green_red_issues,
        n_systems_up_down,
    )
    task_types, n_task_types, n_event_times = _adjust_task_types(
        task_types=task_types, event_times=event_times
    )
    _generate_tasks(
        root=root,
        task_types=task_types,
        event_times=event_times,
        comm_stems_per_ship=comm_stems_per_ship,
        min_seconds_fail_fix_resman=min_seconds_fail_fix_resman,
        max_seconds_fail_fix_resman=max_seconds_fail_fix_resman,
        session_duration_seconds=session_duration_seconds,
        seconds_before_comm_stop=seconds_before_comm_stop,
        seconds_after_comm_start=seconds_after_comm_start,
    )
    _update_xml_with_text_file(root, text_file)
    _generate_auto_and_comm_start_stop(
        root=root,
        session_duration_seconds=session_duration_seconds,
        total_auto_minutes=total_auto_minutes,
        min_seconds_to_indicate_no_comm=min_seconds_to_indicate_no_comm,
        seconds_before_comm_stop=seconds_before_comm_stop,
        seconds_after_comm_start=seconds_after_comm_start,
    )
    xml_string = _finalize_matbii_generation(
        root=root,
        session_duration_seconds=session_duration_seconds,
        xml_declaration=xml_declaration,
    )
    return xml_string, n_task_types, n_event_times


def _update_xml_with_text_file(root, text_file):
    new_root_comms_sysmon = convert_text_file(text_file)

    # Remove old communications and sysmon events from the old root
    for event_type in ["sysmon", "comm"]:
        root = _remove_events(root=root, event_type=event_type)

    # Add communications and sysmon events from new root_comms_sysmon
    root.extend(new_root_comms_sysmon)

    return root


def _remove_events(root, event_type: str):
    root[:] = [event for event in root if not event.find(event_type)]
    return root


def convert_communications_to_xml(time, action, comm_stems_path=None):

    event = Element("event", startTime=time)
    comm = SubElement(event, "comm")
    ship = action.upper()
    SubElement(comm, "ship").text = ship

    # Get communication stems
    comm_stems = _get_comm_stems(comm_stems_path)
    comm_stem = random.choice(comm_stems[ship])

    split_comm_stem = comm_stem.split("_")
    radio = split_comm_stem[1]
    freq = split_comm_stem[2].split("-")[0] + "." + split_comm_stem[2].split("-")[1]
    SubElement(comm, "radio").text = radio.upper()
    SubElement(comm, "freq").text = freq

    return event


def convert_sysmon_lights_to_xml(time, action):
    event = Element("event", startTime=time)
    sysmon = SubElement(event, "sysmon", activity="START")
    light_number = action.split("-")[1]
    light_color = "GREEN" if "1" in light_number else "RED"
    SubElement(sysmon, "monitoringLightType").text = light_color
    return event


def convert_sysmon_scales_to_xml(time, action):
    event = Element("event", startTime=time)
    sysmon = SubElement(event, "sysmon")
    scale_number = action.split("-")[1]
    scale_number_text = ["ONE", "TWO", "THREE", "FOUR"][int(scale_number) - 1]
    SubElement(sysmon, "monitoringScaleNumber").text = scale_number_text
    SubElement(sysmon, "monitoringScaleDirection").text = random.choice(["UP", "DOWN"])
    return event


def convert_text_file(text_file):
    # Read the text file
    with open(text_file, "r") as f:
        lines = f.readlines()

    # Prepare the XML file
    root = Element("MATB-EVENTS")

    # Process each line
    for line in lines:
        if line.startswith("#") or line.strip() == "":
            continue

        # Extract the data
        split_line = re.split(";|\n", line)
        time, task, action = split_line[:3]
        converted_time = _format_seconds(_parse_time_string(time))
        if len(split_line) > 3:
            info = split_line[3]

        # Add to the XML file
        if task == "sysmon":
            if "scales-" in action:
                event = convert_sysmon_scales_to_xml(converted_time, action)
                root.append(event)
            elif "lights-" in action:
                event = convert_sysmon_lights_to_xml(converted_time, action)
                root.append(event)

        elif task == "communications" and action == "radioprompt":
            event = convert_communications_to_xml(converted_time, info)
            root.append(event)

    return root
