import json
from pathlib import Path
from typing import Dict

import pytest

from matbexp.misc.utils import import_dict_from_json


class TestImportDictFromJson:
    @staticmethod
    @pytest.fixture
    def json_file(tmp_path: Path) -> Path:
        """Fixture for creating a JSON file.

        Args:
            tmp_path (Path): Temporary path provided by pytest.

        Returns:
            Path: Path to the created JSON file.
        """
        data = {"key1": "value1", "key2": "value2"}
        file = tmp_path / "data.json"
        with open(file, "w") as f:
            json.dump(data, f)
        return file

    @staticmethod
    @pytest.fixture
    def empty_json_file(tmp_path: Path) -> Path:
        """Fixture for creating a non-JSON file.

        Args:
            tmp_path (Path): Temporary path provided by pytest.

        Returns:
            Path: Path to the created non-JSON file.
        """
        data: Dict[str, str] = {}
        file = tmp_path / "empty.json"
        with open(file, "w") as f:
            json.dump(data, f)
        return file

    @staticmethod
    @pytest.fixture
    def non_json_file(tmp_path: Path) -> Path:
        """Fixture for creating a non-JSON file.

        Args:
            tmp_path (Path): Temporary path provided by pytest.

        Returns:
            Path: Path to the created non-JSON file.
        """
        file = tmp_path / "data.txt"
        file.write_text("This is not a JSON file.")
        return file

    def test_import_dict_from_json(self, json_file: Path) -> None:
        """Test import_dict_from_json with a JSON file.

        Args:
            json_file (Path): Path to the JSON file to import.
        """
        result = import_dict_from_json(json_file)
        assert isinstance(result, dict), "Output should be a dictionary."
        assert result == {
            "key1": "value1",
            "key2": "value2",
        }, "Output dictionary should match the contents of the JSON file."

    def test_import_dict_from_json_empty(self, empty_json_file: Path) -> None:
        """Test import_dict_from_json with a non-JSON file.

        Args:
            non_json_file (Path): Path to the non-JSON file to import.
        """
        result = import_dict_from_json(empty_json_file)
        assert isinstance(result, dict), (
            "Output should be a dictionary even if the input file contains an empty"
            + " dictionary."
        )
        assert result == {}, (
            "Output dictionary should be empty if the input file contains an empty"
            + " dictionary."
        )

    def test_import_dict_from_json_non_dict(self, non_json_file: Path) -> None:
        """Test import_dict_from_json with a non-JSON file.

        Args:
            non_json_file (Path): Path to the non-JSON file to import.
        """
        result = import_dict_from_json(non_json_file)
        assert isinstance(result, dict), (
            "Output should be a dictionary even if the input file does not contain a"
            + " dictionary."
        )
        assert "data" in result.keys(), "Output dictionary should contain the key data."
