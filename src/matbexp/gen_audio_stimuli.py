from pathlib import Path

import pandas as pd

from matbexp.misc.utils import get_repo_location
from matbexp.stimuli import audio_stimuli

_KUMAR_2008_SOUND_NAMES = [
    "Knife bottle",
    "Fork glass",
    "Blackboard chalk",
    "Fork glass",
    "Fork bottle",
    "Blackboard chalk",
    "Ruler bottle",
    "Fork bottle",
    "Ruler bottle",
    "Fork bottle",
    "Female scream",
    "Female scream",
    "Brake double",
    "Fork glass",
    "Blackboard nails",
    "Spade drag",
    "Guitar",
    "Angle grind",
    "Blackboard nails",
    "Clarinet Squeak",
    "Spade drag",
    "Electric drill",
    "Mixer glass",
    "Tire skids",
    "Baby cry",
    "Electric drill",
    "Multiple babies crying",
    "Cat screaming",
    "Violin",
    "Pig",
    "Angle grind",
    "Lion cub",
    "Domestic cat",
    "Record scratch",
    "Jungle bird",
    "Falcon",
    "Buzzer",
    "Panther",
    "Cougar",
    "Wasp",
    "Macaca fascicularis",
    "Glass breaking",
    "Bear",
    "Anteater",
    "Hippo",
    "Lion",
    "Spade drop",
    "Gorilla",
    "Camel",
    "Zebra",
    "Film projector",
    "Bull frog",
    "Eagle",
    "Puffer",
    "Fire alarm",
    "Clarinet honk",
    "Cat purr",
    "Leopard",
    "Elephant",
    "Phone ringing",
    "Howling wolf",
    "Dog growl",
    "Thunder 1",
    "Dolphin clicks",
    "Guitar",
    "Lamb",
    "Thunder 2",
    "Applause",
    "Revving engine",
    "Running water",
    "Bubbling water",
    "Small waterfall",
    "Water flow",
    "Baby laugh",
]

_KUMAR_2008_FILE_NAMES = [
    "knife_bottle_1_db.wav",
    "fork_glass_1_db.wav",
    "blackboard_chalk_1_db.wav",
    "fork_glass_1_db.wav",
    "fork_bottle_1_db.wav",
    "blackboard_chalk_1_db.wav",
    "ruler_bottle_1_db.wav",
    "fork_bottle_1_db.wav",
    "ruler_bottle_1_db.wav",
    "fork_bottle_1_db.wav",
    "femalescream_db.wav",
    "femalescream_db.wav",
    "brake_double_db.wav",
    "fork_glass_1_db.wav",
    "blackboard_nails_1_db.wav",
    "spade_drag_1_db.wav",
    "guitar_1_db.wav",
    "angle_grind_2_db.wav",
    "blackboard_nails_1_db.wav",
    "clarinet_squeak_db.wav",
    "spade_drag_1_db.wav",
    "electric_drill_db.wav",
    "mixer_glass_1_db.wav",
    "tire_skids_db.wav",
    "baby_cry_db.wav",
    "electric_drill_db.wav",
    "multiple_babies_db.wav",
    "cat_screaming_db.wav",
    "violin_db.wav",
    "pig_db.wav",
    "angle_grind_2_db.wav",
    "lion_cub_db.wav",
    "domestic_cat_db.wav",
    "record_scratch_1_db.wav",
    "jungle_bird_db.wav",
    "falcon_db.wav",
    "buzzer_db.wav",
    "panther_db.wav",
    "cougar_db.wav",
    "wasp_db.wav",
    "macaca_fascicularis_db.wav",
    "glass_breaking_db.wav",
    "bear_db.wav",
    "anteater_db.wav",
    "hippo_db.wav",
    "lion_db.wav",
    "spade_drop_1_db.wav",
    "gorilla_db.wav",
    "camel_db.wav",
    "zebra_db.wav",
    "film_projector_db.wav",
    "bull_frog_db.wav",
    "eagle_db.wav",
    "puffer_db.wav",
    "fire_alarm_db.wav",
    "clarinet_honk_db.wav",
    "cat_purr_db.wav",
    "leopard_db.wav",
    "elephant_db.wav",
    "phone_ringing_db.wav",
    "howling_wolf_db.wav",
    "dog_growl_db.wav",
    "thunder1_db.wav",
    "dolphinclicks_db.wav",
    "guitar_2_db.wav",
    "lamb_db.wav",
    "thunder2_db.wav",
    "applause_db.wav",
    "revving_engine_db.wav",
    "running_water_db.wav",
    "bubbling_water_db.wav",
    "small_waterfall_db.wav",
    "water_flow_db.wav",
    "baby_laugh_db.wav",
]
df = pd.DataFrame(
    {
        "Name": _KUMAR_2008_SOUND_NAMES[: len(_KUMAR_2008_FILE_NAMES)],
        "File": _KUMAR_2008_FILE_NAMES,
    }
)

# Configuration
input_folder = Path(
    get_repo_location(), "data", "Kumar_et_al_2008_stimuli/all_project_sounds"
)
sample_rate = 44100
# Range of silence durations in seconds
silence_range = (3.0, 15.0)
# Transition duration in seconds
# (for not having a harsh transition between silence and sound onset/offset)
transition_duration = 0.1
output_folder = Path(
    get_repo_location(), "data/outputs/requin_2023/stress_audio/generated"
)
Path(output_folder).mkdir(parents=True, exist_ok=True)
for version in ["a", "b", "c"]:
    if version == "a":
        random_state = 1
    elif version == "b":
        random_state = 2
    elif version == "c":
        random_state = 3
    # Generate the merged audio file
    output_file = str(
        Path(
            output_folder,
            "stress_audio_stimuli_" + version + "_seed" + str(random_state) + ".wav",
        )
    )
    audio_stimuli.merge_wav_files(
        input_folder=input_folder,
        output_file=output_file,
        silence_range=silence_range,
        transition_duration=transition_duration,
        total_duration_minutes=13,
        sound_file_names=list(df["File"].values[:20]),
        random_state=random_state,
    )
