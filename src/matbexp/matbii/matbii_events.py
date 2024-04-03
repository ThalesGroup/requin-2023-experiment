from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring  # noqa S405

import numpy as np

from ..misc.random import seed_everything
from .matbii_helpers import (
    _format_seconds,
    _get_matbii_comm_stems,
    _has_repeated_values,
    _pretty_format_xml,
    _sort_events_by_seconds,
)
from .matbii_tasks import (
    _generate_all_comm_start_stop,
    _generate_auto_task,
    _generate_random_tasks,
)

_INITIAL_XML_STRING_MATBII = """<MATB-EVENTS>
<!-- Start Resource Management and System Monitoring tasks -->
<event startTime="0:00:01">
    <sched>
        <task>RESSYS</task>
        <action>START</action>
        <update>NULL</update>
        <response>NULL</response>
    </sched>
</event>
<!-- Sched task: TRACK START -->
<event startTime="0:00:02">
    <sched>
        <task>TRACK</task>
        <action>MANUAL</action>
        <update>HIGH</update>
        <response>MEDIUM</response>
    </sched>
</event>
</MATB-EVENTS>"""

_N_ATTEMPTS_CHECK_TASK_TIME_COMPLY = 100000
_GRACE_SECONDS_BEFORE_SESSION_DURATION = 25


def _get_comm_stems(comm_stems_path: Optional[str]) -> Dict[str, List[str]]:
    """
    Get communication stems for each call sign.

    This function retrieves the stems of communication files for each call sign ("own"
    and "other"). The stems are shuffled for randomness. If a path to the stems is
    provided, it will be used. Otherwise, the function will use the default MATBII
    communication stems.

    Args:
        comm_stems_path (str, optional): Path to the communication stems. If None, use
            default MATBII stems.

    Returns:
        dict: A dictionary with call signs as keys ("OWN", "OTHER") and lists of
            communication stems as values.
    """
    comm_stems_per_ship = {}
    for ship in ["own", "other"]:
        if comm_stems_path is not None:
            current_comm_stems = np.array(
                [
                    p.stem
                    for p in Path(comm_stems_path).rglob("*.wav")
                    if ship.upper() in p.stem and len(p.stem.split("_")) == 3
                ]
            )
        else:
            current_comm_stems = np.array(_get_matbii_comm_stems()[ship])
        np.random.shuffle(current_comm_stems)
        comm_stems_per_ship[ship.upper()] = list(current_comm_stems)
    return comm_stems_per_ship


def _initialize_matbii_generation(
    random_state: Optional[int] = None, comm_stems_path: Optional[str] = None
) -> Tuple[str, Element, Dict[str, List[str]]]:
    if random_state is not None:
        seed_everything(random_state)
    xml_declaration = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    root = fromstring(_INITIAL_XML_STRING_MATBII)  # noqa S314
    start_event = SubElement(root, "event", startTime="0:00:00")
    SubElement(start_event, "control").text = "START"
    comm_stems_per_ship = _get_comm_stems(comm_stems_path)
    return xml_declaration, root, comm_stems_per_ship


def _generate_event_times_and_task_types(
    session_duration_minutes: int,
    min_seconds_event_diff: int,
    max_seconds_event_diff: int,
    n_pump_failures: int,
    n_own_comm: int,
    n_other_comm: int,
    n_green_red_issues: int,
    n_systems_up_down: int,
) -> Tuple[int, np.ndarray, np.ndarray]:
    """
    Generate event times and task types.

    This function generates the event times and task types for the given session
    duration and task parameters.

    Args:
        session_duration_minutes (int): The duration of the session in minutes.
        min_seconds_event_diff (int): The minimum time difference between events in
            seconds.
        max_seconds_event_diff (int): The maximum time difference between events in
            seconds.
        n_pump_failures (int): The number of pump failures.
        n_own_comm (int): The number of own communications tasks.
        n_other_comm (int): The number of other communications tasks.
        n_green_red_issues (int): The number of green/red system monitoring tasks.
        n_systems_up_down (int): The number of up/down system monitoring tasks.

    Returns:
        Tuple[int, np.ndarray, np.ndarray]: A tuple containing the session duration in
            seconds, the array of event times, and the array of task types.
    """
    session_duration_seconds = session_duration_minutes * 60
    event_times = generate_random_events(
        min_seconds_event_diff, max_seconds_event_diff, session_duration_seconds
    )
    task_types = generate_task_types(
        n_pump_failures, n_own_comm, n_other_comm, n_green_red_issues, n_systems_up_down
    )
    return session_duration_seconds, event_times, task_types


def _adjust_task_types(
    task_types: np.ndarray, event_times: np.ndarray
) -> Tuple[np.ndarray, int, int]:
    """
    Adjusts the task types to match the number of event times.

    If the number of task types is greater than the number of event times, it trims the
    task types to match the number of event times. If the number of task types is less
    than the number of event times, it appends random task types to match the number of
    event times.

    Args:
        task_types (np.ndarray): The array of task types.
        event_times (np.ndarray): The array of event times.

    Returns:
        Tuple[np.ndarray, int, int]: A tuple containing the adjusted array of task
            types, the original number of task types, and the number of event times.
    """
    n_task_types = len(task_types)
    n_event_times = len(event_times)
    if len(task_types) > len(event_times):
        task_types = task_types[: len(event_times)]
    elif len(task_types) < len(event_times):
        for _ in range(len(event_times) - len(task_types)):
            task_types = np.append(
                task_types,
                np.random.choice(
                    ["resman", "sysmon-light", "sysmon-scale", "comm-own", "comm-other"]
                ),
            )
    return task_types, n_task_types, n_event_times


def _generate_tasks(
    root: Element,
    task_types: np.ndarray,
    event_times: np.ndarray,
    comm_stems_per_ship: Dict[str, List[str]],
    min_seconds_fail_fix_resman: int,
    max_seconds_fail_fix_resman: int,
    session_duration_seconds: int,
    seconds_before_comm_stop: int,
    seconds_after_comm_start: int,
) -> None:
    """
    Generate tasks for the MATB-II.

    Args:
        root (Element): The root element of the XML document.
        task_types (np.ndarray): The array of task types.
        event_times (np.ndarray): The array of event times.
        comm_stems_per_ship (Dict[str, List[str]]): A dictionary with call signs as
            keys ("OWN", "OTHER") and lists of communication stems as values.
        min_seconds_fail_fix_resman (int): The minimum time difference between the fail
            and fix tasks in the Resource Management event.
        max_seconds_fail_fix_resman (int): The maximum time difference between the fail
            and fix tasks in the Resource Management event.
        session_duration_seconds (int): The duration of the session in seconds.
        seconds_before_comm_stop (int): How many seconds should be before the
            indication of stopping communication.
        seconds_after_comm_start (int): How many seconds after the indication of
            starting communication.
    """
    pump_failed_dict = {}
    for i in range(9):
        pump = "P" + str(i)
        pump_failed_dict[pump] = np.zeros(session_duration_seconds)
    task_times_comply = ensure_task_times_comply(
        task_types,
        event_times,
        seconds_before_comm_stop,
        seconds_after_comm_start,
        min_seconds_fail_fix_resman,
        session_duration_seconds,
    )
    if task_times_comply:
        _generate_random_tasks(
            root,
            task_types=task_types,
            event_times=event_times,
            comm_stems_per_ship=comm_stems_per_ship,
            min_seconds_fail_fix_resman=min_seconds_fail_fix_resman,
            max_seconds_fail_fix_resman=max_seconds_fail_fix_resman,
            pump_failed_dict=pump_failed_dict,
        )


def _generate_auto_and_comm_start_stop(
    root: Element,
    session_duration_seconds: int,
    total_auto_minutes: int,
    min_seconds_to_indicate_no_comm: int,
    seconds_before_comm_stop: int,
    seconds_after_comm_start: int,
) -> None:
    """
    Generate period of tracking task automation and communication start/stop events.

    This function generates tracking task automation for the given session duration and
        parameters. It also generates events to indicate the start and stop of
        communication tasks.

    Args:
        root (Element): The root element of the XML document.
        session_duration_seconds (int): The duration of the session in seconds.
        total_auto_minutes (int): The total duration of tracking task automation in
            minutes.
        min_seconds_to_indicate_no_comm (int): The minimum time difference required
            between two communication tasks to indicate to the participant that there is
            no communication for this interval.
        seconds_before_comm_stop (int): How many seconds should be before the
            indication of stopping communication, following the last communication task
            in a long interval. This should also be the minimum time difference between
            the last communication task and the end of the experiment.
        seconds_after_comm_start (int): How many seconds after the indication of
            starting communication that the first communication in a long interval
            should start.
    """
    buffer_seconds_auto = 5
    max_seconds_auto = (
        session_duration_seconds - total_auto_minutes * 60 - buffer_seconds_auto
    )
    min_seconds_auto = buffer_seconds_auto
    auto_start_seconds = np.random.choice(np.arange(min_seconds_auto, max_seconds_auto))
    _generate_auto_task(
        root,
        auto_start_seconds=auto_start_seconds,
        total_auto_minutes=total_auto_minutes,
        session_duration_seconds=session_duration_seconds,
    )
    _generate_all_comm_start_stop(
        root=root,
        min_seconds_to_indicate_no_comm=min_seconds_to_indicate_no_comm,
        seconds_before_comm_stop=seconds_before_comm_stop,
        seconds_after_comm_start=seconds_after_comm_start,
        session_duration_seconds=session_duration_seconds,
    )


def _finalize_matbii_generation(
    root: Element, session_duration_seconds: int, xml_declaration: str
) -> str:
    """
    Finalizes the generation of the MATBII XML string.

    This function adds the final events to the root element and then sorts all events by
    their start times. It then converts the root element to a string, formats it, and
    returns it.

    Args:
        root (Element): The root element of the XML document.
        session_duration_seconds (int): The duration of the session in seconds.
        xml_declaration (str): The XML declaration string.

    Returns:
        str: The generated XML string.
    """
    start_time = _format_seconds(session_duration_seconds - 2)
    event = SubElement(root, "event", startTime=start_time)
    SubElement(event, "rate").text = "START"
    end_time = _format_seconds(session_duration_seconds)
    end_event = SubElement(root, "event", startTime=end_time)
    SubElement(end_event, "control").text = "END"
    root = _sort_events_by_seconds(root=root)
    xml_string = _pretty_format_xml(
        tostring(root, encoding="utf-8").decode("utf-8"),
        xml_declaration=xml_declaration,
    )
    return xml_string


def matbii_generate_random_xml(
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


def generate_random_events(
    min_seconds_event_diff: int,
    max_seconds_event_diff: int,
    session_duration_seconds: int,
) -> np.ndarray:
    """
    Generate random events.

    Args:
        min_seconds_event_diff (int): The minimum time difference between events in
            seconds.
        max_seconds_event_diff (int): The maximum time difference between events in
            seconds.
        session_duration_seconds (int): The duration of the session in seconds.

    Returns:
        np.ndarray: The array of event times.
    """
    size = int(np.round(session_duration_seconds / min_seconds_event_diff))
    event_diffs = np.random.choice(
        np.arange(min_seconds_event_diff, max_seconds_event_diff),
        size=size,
        replace=True,
    )
    event_times = np.cumsum(event_diffs)
    event_times = event_times[
        event_times <= session_duration_seconds - _GRACE_SECONDS_BEFORE_SESSION_DURATION
    ]
    return event_times


def generate_task_types(
    n_pump_failures: int,
    n_own_comm: int,
    n_other_comm: int,
    n_green_red_issues: int,
    n_systems_up_down: int,
) -> np.ndarray:
    """
    Generate task types.

    Args:
        n_pump_failures (int): The number of pump failures.
        n_own_comm (int): The number of own communications tasks.
        n_other_comm (int): The number of other communications tasks.
        n_green_red_issues (int): The number of green/red system monitoring tasks.
        n_systems_up_down (int): The number of systems up/down system monitoring tasks.

    Returns:
        np.ndarray: The array of task types.
    """
    task_types_list = ["resman"] * n_pump_failures
    task_types_list.extend(["comm-own"] * n_own_comm)
    task_types_list.extend(["comm-other"] * n_other_comm)
    task_types_list.extend(["sysmon-light"] * n_green_red_issues)
    task_types_list.extend(["sysmon-scale"] * n_systems_up_down)
    return np.array(task_types_list)


def ensure_task_times_comply(
    task_types: np.ndarray,
    event_times: np.ndarray,
    seconds_before_comm_stop: int,
    seconds_after_comm_start: int,
    min_seconds_fail_fix_resman: int,
    session_duration_seconds: int,
) -> bool:
    """
    Ensure task times comply with certain conditions.

    Args:
        task_types (np.ndarray): The array of task types.
        event_times (np.ndarray): The array of event times.
        seconds_before_comm_stop (int): How many seconds should be before the
            indication of stopping communication.
        seconds_after_comm_start (int): How many seconds after the indication of
            starting communication.
        min_seconds_fail_fix_resman (int): The minimum time difference between the fail
            and fix tasks in the Resource Management event.
        session_duration_seconds (int): The duration of the session in seconds.

    Returns:
        bool: True if task times comply, False otherwise.
    """
    attempts = 0
    task_times_comply = False
    while not task_times_comply and attempts < _N_ATTEMPTS_CHECK_TASK_TIME_COMPLY:
        # Reshuffle
        np.random.shuffle(task_types)
        task_times_comply = _check_task_times_comply(
            task_types=task_types,
            event_times=event_times,
            seconds_before_comm_stop=seconds_before_comm_stop,
            seconds_after_comm_start=seconds_after_comm_start,
            min_seconds_fail_fix_resman=min_seconds_fail_fix_resman,
            session_duration_seconds=session_duration_seconds,
            max_repeats=2,
            window_size=3,
        )
        attempts += 1
    return task_times_comply


def _check_task_times_comply(
    task_types: np.ndarray,
    event_times: np.ndarray,
    seconds_before_comm_stop: int,
    seconds_after_comm_start: int,
    min_seconds_fail_fix_resman: int,
    min_seconds_between_comm: int = 30,
    min_seconds_between_sysmon_light: int = 15,
    min_seconds_between_sysmon_scale: int = 10,
    session_duration_seconds: int = 600,
    max_repeats: int = 2,
    window_size: int = 3,
) -> bool:
    max_seconds_last_comm = session_duration_seconds - seconds_before_comm_stop
    should_not_be_comm = list(
        task_types[np.where(event_times >= max_seconds_last_comm)]
    )
    should_not_be_comm.extend(
        list(task_types[np.where(event_times <= seconds_after_comm_start)])
    )
    comm_times = event_times[
        np.where([t in ["comm-own", "comm-other"] for t in task_types])
    ]

    should_not_be_resman = list(
        task_types[
            np.where(
                event_times
                >= session_duration_seconds - min_seconds_fail_fix_resman - 1
            )
        ]
    )

    sysmon_light_times = event_times[np.where(task_types == "sysmon-light")]
    sysmon_scale_times = event_times[np.where(task_types == "sysmon-scale")]

    if np.any([t in ["comm-own", "comm-other"] for t in should_not_be_comm]):
        return False
    elif np.any(np.diff(comm_times) < min_seconds_between_comm):
        return False
    elif np.any([t == "resman" for t in should_not_be_resman]):
        return False
    elif np.any(np.diff(sysmon_light_times) < min_seconds_between_sysmon_light):
        return False
    elif np.any(np.diff(sysmon_scale_times) < min_seconds_between_sysmon_scale):
        return False
    elif _has_repeated_values(
        task_types, max_repeats=max_repeats, window_size=window_size
    ):
        return False
    else:
        return True
