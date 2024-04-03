from pathlib import Path
from typing import List, Optional

import numpy as np
import pytest
from pytest import TempPathFactory
from scipy.io import wavfile

from matbexp.misc.random import seed_everything
from matbexp.stimuli.audio_stimuli import (
    generate_silence,
    generate_transition,
    merge_wav_files,
)

RANDOM_STATE = 42


class TestGenerateTransition:
    @staticmethod
    def test_generate_transition_basic() -> None:
        """
        Test the function generate_transition.

        This test case will use a float duration and an integer sampling rate as input
        and expects to receive a numpy array as output.
        """
        duration = 0.5
        sampling_rate = 44100

        result = generate_transition(duration, sampling_rate)

        assert isinstance(result, np.ndarray), "Output should be a numpy array."
        assert len(result) == int(
            duration * sampling_rate
        ), "Length of the output array should be equal to duration times sampling rate."
        assert (result >= 0).all() and (
            result <= 1
        ).all(), "All elements in the output array should be between 0 and 1."
        assert result[0] == 0 and result[-1] == 1, (
            "The first element in the output array should be 0 and the last element"
            + " should be 1."
        )


class TestGenerateSilence:
    @staticmethod
    def test_generate_silence_basic() -> None:
        """
        Test the function generate_silence.

        This test case will use a float duration and an integer sampling rate as input
        and expects to receive a numpy array as output.
        """
        duration = 0.5
        sampling_rate = 44100

        result = generate_silence(duration, sampling_rate)

        assert isinstance(result, np.ndarray), "Output should be a numpy array."
        assert len(result) == int(
            duration * sampling_rate
        ), "Length of the output array should be equal to duration times sampling rate."
        assert (result == 0).all(), "All elements in the output array should be 0."


class TestMergeWavFiles:
    @staticmethod
    @pytest.fixture(scope="session")
    def generated_wav_file_parent_path(tmp_path_factory: TempPathFactory) -> Path:
        """
        Fixture that creates a temporary directory for wav files.

        Args:
            tmp_path_factory (TempPathFactory): Pytest fixture for creating temporary
                directories.

        Returns:
            Path: Path object for the temporary directory.
        """
        tmpdir = Path(tmp_path_factory.mktemp("data"), "wav_files")
        return tmpdir.resolve()

    def _test_merge_wav_files(
        self,
        generated_wav_file_parent_path: Path,
        sound_file_names: Optional[List[str]],
    ) -> None:
        """
        Base test method for merge_wav_files function.

        Args:
            generated_wav_file_parent_path (Path): Path to the temporary directory with
                wav files.
            sound_file_names (Optional[List[str]]): List of sound file names to include
                in the test.
        """
        tmpdir = generated_wav_file_parent_path
        # Create directory if it does not exist
        Path(tmpdir).mkdir(parents=True, exist_ok=True)
        # Create some temporary WAV files
        sample_rate = 44100
        for i in range(3):
            file = tmpdir / f"temp{i}.wav"
            audio = np.random.randint(-32768, 32767, size=sample_rate, dtype=np.int16)
            wavfile.write(str(file), sample_rate, audio)

        # Use the function to merge the WAV files
        output_file = tmpdir / "output.wav"
        merge_wav_files(
            input_folder=str(tmpdir),
            output_file=str(output_file),
            silence_range=(0.1, 0.2),
            transition_duration=0.01,
            total_duration_minutes=1,
            sound_file_names=sound_file_names,
        )

        # Check if the output file was created correctly
        assert output_file.is_file(), "Output file was not created."
        sample_rate_out, audio_out = wavfile.read(str(output_file))
        assert sample_rate_out == sample_rate, "Output file has incorrect sample rate."
        assert (
            len(audio_out) <= sample_rate * 60
        ), "Output file is longer than expected."

    def test_merge_wav_files_without_sound_file_names(
        self, generated_wav_file_parent_path: Path
    ) -> None:
        """
        Test merge_wav_files function without providing sound file names.

        Args:
            generated_wav_file_parent_path (Path): Path to the temporary directory with
                wav files.
        """
        self._test_merge_wav_files(
            generated_wav_file_parent_path, sound_file_names=None
        )

    def test_merge_wav_files_with_sound_file_names(
        self, generated_wav_file_parent_path: Path
    ) -> None:
        """
        Test merge_wav_files function with specific sound file names.

        Args:
            generated_wav_file_parent_path (Path): Path to the temporary directory with
                wav files.
        """
        sound_file_names = [
            f"temp{i}.wav" for i in range(2)
        ]  # Include only the first two files
        self._test_merge_wav_files(generated_wav_file_parent_path, sound_file_names)

    @staticmethod
    def _generate_test_merged_audio(input_folder: str, output_file: str) -> None:
        sound_file_names = [f"audio{i}.wav" for i in range(3)]
        # Define the parameters for function
        # Based on how file in test resources was generated
        silence_range = (1.0, 2.0)
        transition_duration = 0.5
        total_duration_minutes = 0.25
        random_state = RANDOM_STATE
        seed_everything(random_state)
        merge_wav_files(
            input_folder=input_folder,
            output_file=output_file,
            silence_range=silence_range,
            transition_duration=transition_duration,
            total_duration_minutes=total_duration_minutes,
            sound_file_names=sound_file_names,
            random_state=random_state,
        )
