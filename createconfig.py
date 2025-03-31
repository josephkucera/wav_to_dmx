import json
import os

# Vytvoření ukázkového JSON konfiguračního souboru pro VectorClass
sample_config = {
    "default_colors": {
        "bass": [255, 255, 255],
        "midA": [255, 0, 0],
        "midB": [0, 255, 0],
        "midC": [0, 0, 255]
    },
    "tone_colors": {
        "0": [255, 255, 255],
        "1": [255, 0, 0],
        "2": [255, 127, 0],
        "3": [255, 255, 0],
        "4": [0, 255, 0],
        "5": [0, 255, 255],
        "6": [0, 127, 255],
        "7": [0, 0, 255],
        "8": [127, 0, 255],
        "9": [255, 0, 255],
        "10": [255, 0, 127],
        "11": [127, 127, 127]
    }
}

# Zajištění složky
os.makedirs("VectorConfig", exist_ok=True)

# Uložení výchozí konfigurace
config_path = "VectorConfig/default.json"
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(sample_config, f, indent=4)

config_path
