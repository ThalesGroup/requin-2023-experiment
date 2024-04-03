from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from scipy.io import wavfile


def generate_transition(duration: float, sampling_rate: int = 44100) -> np.ndarray:
    """Generate a short ramp up/down for smooth transitions.

    Args:
        duration (float): The duration of the transition in seconds.
        sampling_rate (int): Sampling rate of the audio signal in Hz, by default 44100.

    Returns:
        An array representing the transition ramp.

    """
    num_samples = int(duration * sampling_rate)
    ramp = np.linspace(0, 1, num_samples)
    return ramp


def generate_silence(duration: float, sampling_rate: int = 44100) -> np.ndarray:
    """Generate silence for a given duration.

    Args:
        duration (float): The duration of the silence in seconds.
        sampling_rate (int): Sampling rate of the audio signal in Hz, by default 44100.

    Returns:
        An array representing the silence.

    """
    num_samples = int(duration * sampling_rate)
    silence = np.zeros(num_samples)
    return silence


def merge_wav_files(
    input_folder: str,
    output_file: str,
    silence_range: Tuple[float, float],
    transition_duration: float,
    total_duration_minutes: int,
    sound_file_names: Optional[list] = None,
    random_state: Optional[int] = None,
) -> None:
    """Merge WAV files with silence intervals.

    Args:
        input_folder (str): Path to the folder containing WAV files.
        output_file (str): Path to the output merged WAV file.
        silence_range (Tuple[float, float]): Range of silence durations between sounds
            in seconds.
        transition_duration (float): Duration of the transition ramp in seconds.
        total_duration_minutes (int): Desired duration of the output file in minutes.
        sound_file_names (Optional[list]): A list of sound file names to be included,
            e.g. ``["angle_grind1_db.wav"]``.
        random_state (Optional[int]): Random seed for the random number generator.
            If provided, it ensures reproducibility by setting the seed. Default is
            ``None``, which results in non-reproducible random numbers.
    """
    files = [str(p) for p in Path(input_folder).rglob("*.wav")]
    if sound_file_names is not None:
        files = [f for f in files if Path(f).name in sound_file_names]

    audio_list = []
    longer_than_total_duration = False
    rng = np.random.default_rng(seed=random_state)

    while not longer_than_total_duration:
        file = rng.choice(files)
        sample_rate, audio = wavfile.read(file)

        # Normalize the audio to the range [-1, 1]
        audio = np.array(audio).astype(np.float32) / np.iinfo(np.array(audio).dtype).max

        # Generate transition and silence durations
        transition = generate_transition(transition_duration, sampling_rate=sample_rate)
        silence_duration = rng.uniform(*silence_range)
        silence = generate_silence(silence_duration, sampling_rate=sample_rate)

        # Apply transition and silence to audio
        transition_length = len(transition)
        audio[:transition_length] *= transition

        audio = np.concatenate((audio, silence))
        audio_list.append(audio)
        merged_audio = np.concatenate(audio_list)
        if len(merged_audio) > total_duration_minutes * 60 * sample_rate:
            longer_than_total_duration = True

    merged_audio = (merged_audio * np.iinfo(np.int16).max).astype(np.int16)

    merged_audio = merged_audio[: int(total_duration_minutes * 60 * sample_rate)]

    # Create parent directory of output path if it does not exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(output_file, sample_rate, merged_audio)
