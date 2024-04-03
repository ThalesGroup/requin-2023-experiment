import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
from pytest import TempPathFactory

from matbexp.gen_matbii_events import _create_matbii_scenarios
from matbexp.matbii.matbii_events import _check_task_times_comply


class TestMatbiiGenerateRandomXml:
    def _generate_regression_files(self, output_folder: Path) -> None:
        # Generate files for both conditions
        _create_matbii_scenarios(condition="high", output_folder=output_folder)
        _create_matbii_scenarios(condition="low", output_folder=output_folder)

    @staticmethod
    def _test_xml_same(xml1: str, xml2: str) -> None:
        # Parse the XML documents into ElementTree objects
        tree1 = ET.fromstring(xml1)
        tree2 = ET.fromstring(xml2)

        # Compare the root tag
        assert tree1.tag == tree2.tag

        # Compare the number of child elements
        assert len(tree1) == len(tree2)

        # Compare each child element
        for child1, child2 in zip(tree1, tree2):
            assert child1.tag == child2.tag
            assert child1.text == child2.text

    @staticmethod
    @pytest.fixture(scope="session")
    def generated_output_file_parent_path(tmp_path_factory: TempPathFactory) -> Path:
        """
        Fixture that creates a temporary directory for output files.

        Args:
            tmp_path_factory (TempPathFactory): Pytest fixture for creating temporary
                directories.

        Returns:
            Path: Path object for the temporary directory.
        """
        tmpdir = Path(tmp_path_factory.mktemp("data"), "output_files")
        return tmpdir.resolve()

    def test_matbii_generate_random_xml_regression(
        self, generated_output_file_parent_path: Path
    ) -> None:
        """
        Test the generation of random XML files for MATBII and compare with expected files.

        Args:
            generated_output_file_parent_path (Path): Path to the directory where generated
                XML files are stored.

        Raises:
            AssertionError: If the generated XML files do not match the expected files.
        """
        # Load the expected XML files
        expected_xml_parent_path = Path(__file__).parents[1] / "resources"
        expected_xml_files = [
            xml_path
            for xml_path in expected_xml_parent_path.rglob("*.xml")
            if "MATB_EVENTS" in xml_path.name
        ]
        assert len(expected_xml_files) > 0

        _create_matbii_scenarios(
            condition="high", output_folder=generated_output_file_parent_path
        )
        _create_matbii_scenarios(
            condition="low", output_folder=generated_output_file_parent_path
        )

        # Match generated and expected XML files by their file names
        generated_xml_files = [
            xml_path
            for xml_path in generated_output_file_parent_path.rglob("*.xml")
            if "MATB_EVENTS" in xml_path.name
        ]
        for expected_xml_file in expected_xml_files:
            matched_files = [
                generated_xml_file
                for generated_xml_file in generated_xml_files
                if expected_xml_file.stem == generated_xml_file.stem
            ]
            if matched_files:
                with open(expected_xml_file, "r") as file:
                    expected_xml = file.read()
                with open(matched_files[0], "r") as file:
                    generated_xml = file.read()
                # Confirm that they are the same with self._test_xml_same()
                self._test_xml_same(expected_xml, generated_xml)


def test_check_task_times_comply() -> None:
    """
    Test the compliance of task times in different scenarios.

    Raises:
        AssertionError: If the task times do not comply with the expected behavior.
    """
    # Check should fail due to comm start being too late
    # relative to the end of the session
    task_types = np.array(
        [
            "resman",
            "sysmon-light",
            "sysmon-scale",
            "resman",
            "comm-other",
            "sysmon-scale",
        ]
    )
    event_times = np.array([5, 20, 40, 50, 75, 80])
    seconds_before_comm_stop = 30
    seconds_after_comm_start = 5
    session_duration_seconds = 90
    min_seconds_fail_fix_resman = 20
    assert (
        _check_task_times_comply(
            task_types=task_types,
            event_times=event_times,
            seconds_before_comm_stop=seconds_before_comm_stop,
            seconds_after_comm_start=seconds_after_comm_start,
            session_duration_seconds=session_duration_seconds,
            min_seconds_fail_fix_resman=min_seconds_fail_fix_resman,
        )
        is False
    )

    # Check should fail due to comm tasks being too close together
    task_types = np.array(
        [
            "resman",
            "sysmon-scale",
            "comm-own",
            "comm-other",
            "sysmon-light",
            "sysmon-scale",
        ]
    )
    event_times = np.array([5, 20, 40, 50, 60, 80])
    seconds_before_comm_stop = 30
    seconds_after_comm_start = 5
    session_duration_seconds = 90
    assert (
        _check_task_times_comply(
            task_types=task_types,
            event_times=event_times,
            seconds_before_comm_stop=seconds_before_comm_stop,
            seconds_after_comm_start=seconds_after_comm_start,
            session_duration_seconds=session_duration_seconds,
            min_seconds_fail_fix_resman=min_seconds_fail_fix_resman,
        )
        is False
    )

    # Check should fail due to sysmon-light tasks being too close together
    task_types = np.array(
        ["resman", "sysmon-light", "sysmon-light", "comm-own", "sysmon-scale"]
    )
    event_times = np.array([5, 20, 30, 50, 60])
    seconds_before_comm_stop = 30
    seconds_after_comm_start = 5
    session_duration_seconds = 90
    assert (
        _check_task_times_comply(
            task_types=task_types,
            event_times=event_times,
            seconds_before_comm_stop=seconds_before_comm_stop,
            seconds_after_comm_start=seconds_after_comm_start,
            session_duration_seconds=session_duration_seconds,
            min_seconds_fail_fix_resman=min_seconds_fail_fix_resman,
        )
        is False
    )

    # Check should pass
    task_types = np.array(
        ["resman", "sysmon-light", "sysmon-scale", "comm-own", "sysmon-scale"]
    )
    event_times = np.array([5, 20, 40, 50, 60])
    seconds_before_comm_stop = 30
    seconds_after_comm_start = 5
    session_duration_seconds = 90
    assert (
        _check_task_times_comply(
            task_types=task_types,
            event_times=event_times,
            seconds_before_comm_stop=seconds_before_comm_stop,
            seconds_after_comm_start=seconds_after_comm_start,
            session_duration_seconds=session_duration_seconds,
            min_seconds_fail_fix_resman=min_seconds_fail_fix_resman,
        )
        is True
    )
