from pathlib import Path

import pytest
from pytest import TempPathFactory

from matbexp.stimuli.video_stimuli import (
    generate_fixation_cross,
    generate_fixation_video,
)


@pytest.fixture(scope="session")
def generated_fixation_video_path(tmp_path_factory: TempPathFactory) -> Path:
    """
    Pytest fixture that generates a fixation video for testing.

    Args:
        tmp_path_factory (TempPathFactory): pytest fixture for creating temporary directories.

    Returns:
        Path: The path to the generated video file.
    """
    output_video_path = Path(
        tmp_path_factory.mktemp("data"), "outputs/output_video.mp4"
    )

    fade_seconds = 2
    duration_seconds = 10
    frame_rate = 25

    resolution = (1920, 1080)
    resolution_ratio = 0.4
    size_ratio = 0.15
    screen_size = (
        int(resolution[0] * resolution_ratio),
        int(resolution[1] * resolution_ratio),
    )
    cross_thickness = 5
    cross_color = (255, 255, 255)

    fixation_cross_image = generate_fixation_cross(
        screen_size, size_ratio, cross_thickness, cross_color
    )
    generate_fixation_video(
        fixation_cross_image,
        output_video_path,
        duration_seconds,
        frame_rate,
        fade_seconds=fade_seconds,
    )
    return output_video_path.resolve()


def test_generate_fixation_video(generated_fixation_video_path: Path) -> None:
    """
    Test case for the generate_fixation_video function.

    Args:
        generated_fixation_video_path (Path): The path to the generated video file.

    Raises:
        AssertionError: If the file does not exist at the given path.
    """
    assert generated_fixation_video_path.is_file()
