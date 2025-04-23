import json
import os
from pathlib import Path

class VectorClass:
    def __init__(self, scene_manager, mode="newton", config_dir="VectorConfig"):
        self.scene = scene_manager
        self.mode = mode
        self.config_dir = config_dir
        self.last_freqs = (None, None, None)
        self._last_beat = False
        self.load_mode_config(mode)
        self.switch_state = False

    def load_mode_config(self, mode):
        config_path = Path(self.config_dir) / "modes.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Konfigurační soubor {config_path} neexistuje.")

        with open(config_path, "r", encoding="utf-8") as f:
            all_configs = json.load(f)

        if mode not in all_configs:
            raise ValueError(f"Režim '{mode}' nebyl nalezen v konfiguračním souboru.")

        self.config = all_configs[mode]
        self.default_colors = self.config["default_colors"]
        self.tone_colors = self.config["tone_colors"]

        # Inicializace výchozích barev
        self.scene.set_color_for_group("bass", self.default_colors.get("bass", [255, 255, 255]))
        self.scene.set_color_for_group("midA", self.default_colors.get("midA", [255, 255, 255]))
        self.scene.set_color_for_group("midB", self.default_colors.get("midB", [255, 255, 255]))
        self.scene.set_color_for_group("midC", self.default_colors.get("midC", [255, 255, 255]))

        # Výchozí intenzita pro každou skupinu
        self.scene.set_dim_all(128)

        

    def process_audio_state(self, state):
        # Reakce na beat pouze při hodnotě True
        if state.beat_on_off:
            self.switch_state = not self.switch_state
            self.scene.alternating_light_strip("strip", state=self.switch_state, intensity=200)
            self.scene.pulse_on_beat("bass", intensity=255, duration=0.2)
            self.scene.set_dim_for_group("bass", 128)
        
        # Efekt: střídání ledek

        
    

        # Nastavení barev podle frekvencí (pouze při změně)
        freqs = tuple(state.freqs)
        if len(freqs) >= 3:
            updated = False
            if freqs[0] != self.last_freqs[0]:
                self.scene.set_color_for_group("bass", self.tone_colors.get(str(freqs[0]), [255, 255, 255]))
                self.scene.set_color_for_group("midA", self.tone_colors.get(str(freqs[0]), [255, 255, 255]))
                updated = True
            if freqs[1] != self.last_freqs[1]:
                self.scene.set_color_for_group("midB", self.tone_colors.get(str(freqs[1]), [255, 255, 255]))
                updated = True
            if freqs[2] != self.last_freqs[2]:
                self.scene.set_color_for_group("midC", self.tone_colors.get(str(freqs[2]), [255, 255, 255]))
                updated = True
            self.last_freqs = freqs