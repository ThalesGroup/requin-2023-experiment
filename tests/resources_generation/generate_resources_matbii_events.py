from pathlib import Path

from matbexp.matbii.matbii_events import matbii_generate_random_xml

# Define parameters for different conditions
_MATBII_HIGH_PARAMS = {
    "min_seconds_event_diff": 10,
    "max_seconds_event_diff": 35,
    "session_duration_minutes": 10,
    "min_seconds_fail_fix_resman": 20,
    "max_seconds_fail_fix_resman": 90,
    "min_seconds_to_indicate_no_comm": 90,
    "seconds_before_comm_stop": 30,
    "seconds_after_comm_start": 5,
    "n_pump_failures": 6,
    "n_own_comm": 6,
    "n_other_comm": 6,
    "n_green_red_issues": 7,
    "n_systems_up_down": 7,
    "total_auto_minutes": 3,
}

_MATBII_LOW_PARAMS = {
    "min_seconds_event_diff": 20,
    "max_seconds_event_diff": 70,
    "session_duration_minutes": 10,
    "min_seconds_fail_fix_resman": 20,
    "max_seconds_fail_fix_resman": 90,
    "min_seconds_to_indicate_no_comm": 90,
    "seconds_before_comm_stop": 30,
    "seconds_after_comm_start": 5,
    "n_pump_failures": 2,
    "n_own_comm": 2,
    "n_other_comm": 3,
    "n_green_red_issues": 3,
    "n_systems_up_down": 3,
    "total_auto_minutes": 6,
}


def _create_matbii_scenarios(condition: str, output_folder: Path) -> None:
    seed = 0
    if condition == "high":
        params_dict = _MATBII_HIGH_PARAMS
    elif condition == "low":
        params_dict = _MATBII_LOW_PARAMS
    for version in ["a", "b", "c"]:
        if not ((condition == "high") & (version == "c")):
            n_task_types = -1
            n_event_times = 0

            attempts = 0
            while n_task_types != n_event_times and attempts < 100:
                seed += 1
                attempts += 1
                # Generate a random XML file
                random_xml, n_task_types, n_event_times = matbii_generate_random_xml(
                    random_state=seed, comm_stems_path=None, **params_dict
                )

            # Save the XML to a file
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            if (condition == "low") & (version == "c"):
                file_stem = (
                    "MATB_EVENTS_tutorial_"
                    + str(_MATBII_LOW_PARAMS["session_duration_minutes"])
                    + "mins"
                    + "_seed_"
                    + str(seed)
                )
            else:
                file_stem = (
                    "MATB_EVENTS_" + condition + "_" + version + "_seed_" + str(seed)
                )
            file_path = str(Path(output_folder, file_stem + ".xml"))
            with open(file_path, "w") as file:
                file.write(random_xml)


def main() -> None:
    """
    Main function to generate files for both "high" and "low" conditions.

    This function defines the output folder for the generated files and
    calls the `_create_matbii_scenarios` function for both conditions.

    Returns:
        None
    """
    # Define the folder for the generated files
    output_folder = Path(__file__).parent.parent / "resources"
    # Generate files for both conditions
    _create_matbii_scenarios(condition="high", output_folder=output_folder)
    _create_matbii_scenarios(condition="low", output_folder=output_folder)


if __name__ == "__main__":
    main()
