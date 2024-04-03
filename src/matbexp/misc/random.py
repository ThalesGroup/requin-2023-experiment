import os
import random

import numpy as np


def seed_everything(seed: int) -> None:
    """Set the seed for the random number generators.

    Args:
        seed (int): Seed used for the random number generators.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
