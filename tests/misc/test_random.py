import os
import random

import numpy as np

from matbexp.misc.random import seed_everything


class TestSeedEverything:
    """Class for testing the seed_everything function."""

    @staticmethod
    def test_random_seed() -> None:
        """Test if the seed is correctly set for the random module."""
        seed = 42
        seed_everything(seed)
        assert (
            random.randint(0, 100) == 81
        ), "random.randint does not produce the expected result."

    @staticmethod
    def test_os_seed() -> None:
        """Test if the seed is correctly set for the os module."""
        seed = 42
        seed_everything(seed)
        assert os.environ["PYTHONHASHSEED"] == str(
            seed
        ), "os.environ['PYTHONHASHSEED'] does not match the seed."

    @staticmethod
    def test_np_seed() -> None:
        """Test if the seed is correctly set for the numpy module."""
        seed = 42
        seed_everything(seed)
        assert (
            np.random.randint(0, 100) == 51
        ), "np.random.randint does not produce the expected result."

    @staticmethod
    def test_np_random_function() -> None:
        """Test if a random function in numpy produces the same output after seeding."""
        seed = 42
        seed_everything(seed)
        random_array1 = np.random.random((5, 5))

        # Reset and reapply the seed
        seed_everything(seed)
        random_array2 = np.random.random((5, 5))

        assert np.array_equal(
            random_array1, random_array2
        ), "Random arrays should be the same after reseeding."
