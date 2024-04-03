from typing import List, Optional
from warnings import warn
from xml.etree.ElementTree import Comment, Element, SubElement  # noqa S405

import numpy as np

from .matbii_helpers import _format_seconds, _parse_time_string, _sort_events_by_seconds


def _generate_random_tasks(
    root: Element,
    task_types: np.ndarray,
    event_times: np.ndarray,
    comm_stems_per_ship: dict,
    min_seconds_fail_fix_resman: int,
    max_seconds_fail_fix_resman: int,
    pump_failed_dict: Optional[dict],
) -> None:
    for task_type, event_time in zip(task_types, event_times):
        time = _format_seconds(event_time)

        if task_type == "resman":
            pump_failed_dict = _generate_resman_task(
                root,
                time=time,
                min_seconds_fail_fix=min_seconds_fail_fix_resman,
                max_seconds_fail_fix=max_seconds_fail_fix_resman,
                pump_failed_dict=pump_failed_dict,
            )
        elif task_type.split("-")[0] == "sysmon":
            sysmon_subtype = task_type.split("-")[1]
            _generate_sysmon_task(root, time=time, sysmon_subtype=sysmon_subtype)
        elif task_type.split("-")[0] == "comm":
            ship = task_type.split("-")[1].upper()
            comm_stem = comm_stems_per_ship[ship].pop()
            _generate_comm_task(root, time=time, comm_stem=comm_stem)


def _generate_comm_sched_task(root: Element, time: str, action: str) -> None:
    """Generate a comm Sched task and add it to the event.

    Args:
        root (Element): The parent XML element to add the task to.
        time (str): The time in the format "HH:MM:SS".
        action (str): ``"START"`` or ``"STOP"``.
    """
    comment = Comment("Sched task")

    auto_event = SubElement(root, "event", startTime=time)
    auto_event.append(comment)
    task = SubElement(auto_event, "sched")
    SubElement(task, "task").text = "COMM"
    SubElement(task, "action").text = action
    SubElement(task, "update").text = "NULL"
    SubElement(task, "response").text = "NULL"


def _get_comm_task_times(root: Element) -> List[int]:
    """
    This function extracts the timestamps of communication tasks from
    the given root element.

    Args:
        root (Element): The root element of the XML document.

    Returns:
        List[int]: A list of timestamps of communication tasks.
    """
    # Get all event elements
    event_elements = root.findall("event")

    # Get the timestamps of comm tasks
    comm_task_times = []
    for event in event_elements:
        if event.find("comm") is not None:
            start_time_str = event.attrib["startTime"]
            comm_task_times.append(_parse_time_string(start_time_str))

    return comm_task_times


def _generate_all_comm_start_stop(
    root: Element,
    min_seconds_to_indicate_no_comm: int = 90,
    seconds_before_comm_stop: int = 30,
    seconds_after_comm_start: int = 5,
    session_duration_seconds: int = 600,
) -> None:
    # Get all event elements
    root = _sort_events_by_seconds(root=root)
    comm_task_times = _get_comm_task_times(root=root)

    # Get timestamp of first comm task and set initial communication start
    first_comm_task_time = comm_task_times[0]
    if first_comm_task_time > seconds_after_comm_start:
        first_comm_start_time = first_comm_task_time - seconds_after_comm_start
    else:
        first_comm_start_time = first_comm_task_time
        warn(
            "The first communication is less than "
            + str(seconds_after_comm_start)
            + " seconds after the start of the experiment"
        )
    _generate_comm_sched_task(
        root=root, time=_format_seconds(first_comm_start_time), action="START"
    )

    # Identify intervals with no "comm" task for over 90 seconds
    no_comm_intervals = []
    start_time_num = first_comm_start_time
    for comm_time in comm_task_times:
        diff = comm_time - start_time_num
        if diff > min_seconds_to_indicate_no_comm:
            comm_stop_time = start_time_num + seconds_before_comm_stop
            comm_start_time = comm_time - seconds_after_comm_start
            no_comm_intervals.append((comm_stop_time, comm_start_time))
        start_time_num = comm_time

    # Add comm stop and stop at the beginning and end of long intervals
    for comm_stop_time, comm_start_time in no_comm_intervals:
        _generate_comm_sched_task(
            root=root, time=_format_seconds(comm_stop_time), action="STOP"
        )
        _generate_comm_sched_task(
            root=root, time=_format_seconds(comm_start_time), action="START"
        )

    # Get timestamp of last comm task and set final communication stop
    last_comm_task_time = comm_task_times[-1]
    if session_duration_seconds - last_comm_task_time > seconds_before_comm_stop:
        last_comm_stop_time = last_comm_task_time + seconds_before_comm_stop
    else:
        last_comm_stop_time = session_duration_seconds
        warn(
            "The last communication is at "
            + str(last_comm_task_time)
            + " seconds, which is less than "
            + str(seconds_before_comm_stop)
            + " seconds before the stop of the experiment"
        )
    _generate_comm_sched_task(
        root=root, time=_format_seconds(last_comm_stop_time), action="STOP"
    )


def _generate_auto_task(
    root: Element,
    auto_start_seconds: int = 60,
    total_auto_minutes: int = 5,
    session_duration_seconds: int = 600,
) -> None:
    """Generate an auto Sched task and add it to the event.

    Args:
        root (Element): The parent XML element to add the task to.
        auto_start_seconds (int): The start time of the auto task in seconds.
        total_auto_minutes (int): The total duration of the auto task in minutes.
        session_duration_seconds (int): The duration of the session in seconds. Default
            is 600.
    """
    comment = Comment("Sched task")

    start_time_auto = _format_seconds(auto_start_seconds)
    auto_event = SubElement(root, "event", startTime=start_time_auto)
    auto_event.append(comment)
    task = SubElement(auto_event, "sched")
    SubElement(task, "task").text = "TRACK"
    SubElement(task, "action").text = "AUTO"
    SubElement(task, "update").text = "NULL"
    SubElement(task, "response").text = "NULL"

    start_time_manual = _format_seconds(auto_start_seconds + total_auto_minutes * 60)
    manual_event = SubElement(root, "event", startTime=start_time_manual)
    manual_event.append(comment)
    task = SubElement(manual_event, "sched")
    SubElement(task, "task").text = "TRACK"
    SubElement(task, "action").text = "MANUAL"
    SubElement(task, "update").text = "MEDIUM"
    SubElement(task, "response").text = "HIGH"

    start_time_auto = _format_seconds(session_duration_seconds - 3)
    auto_event = SubElement(root, "event", startTime=start_time_auto)
    auto_event.append(comment)
    task = SubElement(auto_event, "sched")
    SubElement(task, "task").text = "TRACK"
    SubElement(task, "action").text = "AUTO"
    SubElement(task, "update").text = "NULL"
    SubElement(task, "response").text = "NULL"


def _generate_resman_task(
    root: Element,
    time: str,
    min_seconds_fail_fix: int = 20,
    max_seconds_fail_fix: int = 90,
    pump_failed_dict: Optional[dict] = None,
) -> Optional[dict]:
    """Generate a random Resource Management task and add it to the event.

    Args:
        root (Element): The parent XML element to add the task to.
        time (str): The time in the format "HH:MM:SS".
        min_seconds_fail_fix (int): The minimum time difference between the fail and
            fix tasks in seconds.
        max_seconds_fail_fix (int): The maximum time difference between the fail and
            fix tasks in seconds.
        pump_failed_dict (Optional[dict]): Dictionary tracking whether pump has failed
            already.

    Returns:
        Optional[dict]: A dictionary with the pump statuses, or None if no dictionary
            was provided.
    """
    if pump_failed_dict is not None:
        need_to_select_pump = True
        fix_time_seconds = len(pump_failed_dict["P1"])
        while fix_time_seconds >= len(pump_failed_dict["P1"]) - 1:
            diff_seconds_fail_fix = np.random.choice(
                np.arange(min_seconds_fail_fix, max_seconds_fail_fix)
            )
            fail_time_seconds = _parse_time_string(time)
            fix_time_seconds = diff_seconds_fail_fix + fail_time_seconds
        fix_time = _format_seconds(fix_time_seconds)
        while need_to_select_pump:
            pump = "P" + str(np.random.randint(1, 8))
            # If pump did not already fail
            if np.all(pump_failed_dict[pump][fail_time_seconds:fix_time_seconds] == 0):
                pump_failed_dict[pump][fail_time_seconds:fix_time_seconds] = 1
                need_to_select_pump = False
    else:
        pump = "P" + str(np.random.randint(1, 8))

    event_fail = SubElement(root, "event", startTime=time)
    comment_fail = Comment("Resman task - Fail")
    event_fail.append(comment_fail)
    resman_fail = SubElement(event_fail, "resman")
    SubElement(resman_fail, "fail").text = pump

    event_fix = SubElement(root, "event", startTime=fix_time)
    comment_fix = Comment("Resman task - Fix")
    event_fix.append(comment_fix)
    resman_fix = SubElement(event_fix, "resman")
    SubElement(resman_fix, "fix").text = pump
    return pump_failed_dict


def _generate_sysmon_task(
    root: Element, time: str, sysmon_subtype: str = "light"
) -> None:
    """Generate a System Monitoring task and add it to the event.

    Args:
        root (Element): The parent XML element to add the task to.
        time (str): The time in the format "HH:MM:SS".
        sysmon_subtype (str): The subtype of the System Monitoring task. Default is
            ``"light"``.
    """
    event = SubElement(root, "event", startTime=time)
    comment = Comment("System Monitoring task")
    event.append(comment)
    sysmon = SubElement(event, "sysmon")
    if sysmon_subtype == "light":
        color = np.random.choice(["GREEN", "RED"])
        SubElement(sysmon, "monitoringLightType").text = color
        if color == "GREEN":
            sysmon.set("activity", "START")
    else:
        SubElement(sysmon, "monitoringScaleNumber").text = np.random.choice(
            ["ONE", "TWO", "THREE", "FOUR"]
        )
        SubElement(sysmon, "monitoringScaleDirection").text = np.random.choice(
            ["UP", "DOWN"]
        )


def _generate_comm_task(root: Element, time: str, comm_stem: str) -> None:
    """Generate a random Communications task and add it to the event.

    Args:
        root (Element): The parent XML element to add the task to.
        time (str): The time in the format "HH:MM:SS".
        comm_stem (str): The communication file name without the extension.
    """
    event = SubElement(root, "event", startTime=time)
    comment = Comment("Communications task")
    event.append(comment)
    split_comm_stem = comm_stem.split("_")
    ship = split_comm_stem[0]
    radio = split_comm_stem[1]
    freq = split_comm_stem[2].split("-")[0] + "." + split_comm_stem[2].split("-")[1]
    comm = SubElement(event, "comm")
    SubElement(comm, "ship").text = ship
    SubElement(comm, "radio").text = radio
    SubElement(comm, "freq").text = freq
