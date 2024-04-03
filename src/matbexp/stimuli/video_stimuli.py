from pathlib import Path
from typing import Any, Callable, Optional, Tuple, Union

import numpy as np
from moviepy.editor import ImageSequenceClip
from PIL import Image, ImageDraw


def generate_fixation_cross(
    screen_size: Tuple[int, int],
    size_ratio: float,
    thickness: int,
    background_color: Tuple[int, int, int],
) -> Image:
    """
    Generate a fixation cross image with the specified screen size, size ratio,
        thickness, and color.

    Args:
        screen_size (Tuple[int, int]): The screen size (width, height).
        size_ratio (float): The ratio of the fixation cross size to the screen size.
        thickness (int): The thickness of the lines in pixels.
        background_color (Tuple[int, int, int]): The RGBA color tuple for the
            background.

    Returns:
        Image: The generated fixation cross image.

    """
    width, height = screen_size

    # Calculate the shorter dimension based on the aspect ratio
    shorter_dimension = min(width, height)

    # Calculate the size of the cross based on the screen size and the size ratio
    cross_width = int(shorter_dimension * size_ratio)
    cross_height = int(shorter_dimension * size_ratio)

    # Calculate the coordinates for the fixation cross
    x1 = (width - cross_width) // 2
    x2 = x1 + cross_width
    y1 = (height - cross_height) // 2
    y2 = y1 + cross_height

    # Create a new image with the desired size and color
    image = Image.new("RGBA", screen_size, background_color)
    draw = ImageDraw.Draw(image)

    # Draw the horizontal line of the fixation cross
    draw.line(
        [(x1, (y1 + y2) // 2), (x2, (y1 + y2) // 2)], fill=(0, 0, 0), width=thickness
    )

    # Draw the vertical line of the fixation cross
    draw.line(
        [((x1 + x2) // 2, y1), ((x1 + x2) // 2, y2)], fill=(0, 0, 0), width=thickness
    )

    return image


def chunked_operation(
    arr: np.ndarray,
    func: Callable[[np.ndarray, Any], np.ndarray],
    chunk_size: int = 1000,
    *args: Any,
    **kwargs: Any
) -> np.ndarray:
    """
    Perform an operation on a NumPy array in chunks.

    Args:
        arr (numpy.ndarray): The input NumPy array.
        func (Callable[[np.ndarray, Any], np.ndarray]):
            The function to apply to each chunk of the array.
            The function should accept a NumPy array as input and return a NumPy array.
        chunk_size (int): The size of each chunk. Default is 1000.
        *args (Any): Additional positional arguments to pass to the function.
        **kwargs (Any): Additional keyword arguments to pass to the function.

    Returns:
        numpy.ndarray: The modified NumPy array.
    """
    num_chunks = len(arr) // chunk_size

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size
        arr[start_idx:end_idx] = func(arr[start_idx:end_idx], *args, **kwargs)

    # Process the last chunk (if any)
    last_chunk_start = num_chunks * chunk_size
    if last_chunk_start < len(arr):
        arr[last_chunk_start:] = func(arr[last_chunk_start:], *args, **kwargs)

    return arr


def apply_opacity(chunk: np.ndarray, current_opacity: float) -> np.ndarray:
    """
    Apply opacity to a chunk of a NumPy array.

    Args:
        chunk (numpy.ndarray): The input chunk of the NumPy array.
        current_opacity (float): The opacity value.

    Returns:
        numpy.ndarray: The modified chunk after applying opacity.
    """
    return chunk * (current_opacity / 255)


def generate_fixation_video(
    fixation_image: Image,
    output_path: Union[str, Path],
    duration: int = 360,
    frame_rate: int = 30,
    fade_seconds: Optional[float] = None,
) -> None:
    """
    Generate a video with a fading fixation cross effect.

    Args:
        fixation_image (Image): The fixation cross image.
        output_path (Union[str, Path]): The path to save the generated video.
        duration (int): The duration of the video in seconds.
        frame_rate (int): The frame rate of the video.
        fade_seconds (float): The time (in seconds) when the fade effect should start.
            Defaults to None.

    """
    # Calculate the total number of frames in the video
    total_frames = duration * frame_rate

    # Calculate the frame count at which the fade effect should start
    fade_frame_count = (
        int((duration - fade_seconds) * frame_rate) if fade_seconds else 0
    )

    # Create a list to store the frames
    frames = []

    for frame_count in range(total_frames):
        # Calculate current opacity for the fade effect
        current_opacity_initial = int(
            255
            - (
                (frame_count - fade_frame_count)
                * (255 / (total_frames - fade_frame_count))
            )
        )

        # Clip the opacity value to ensure it stays within the valid range
        current_opacity = max(0, min(current_opacity_initial, 255))

        # Create a new frame with the fixation cross image
        frame = Image.new("RGBA", fixation_image.size, (0, 0, 0, 0))
        frame.paste(fixation_image, (0, 0))
        np_frame = np.array(frame)

        # Apply the current opacity to the frame
        result_frame = chunked_operation(
            np_frame, apply_opacity, chunk_size=3, current_opacity=current_opacity
        )

        # Append the frame to the list
        frames.append(result_frame)

    # Create a video clip from the frames
    clip = ImageSequenceClip(frames, fps=frame_rate)

    # Save the video to the specified output path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    clip.write_videofile(str(output_path), codec="libx264", threads=4)
