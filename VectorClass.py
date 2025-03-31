import json
import os
from pathlib import Path

class VectorClass:
    def __init__(self, scene_manager, mode="newton", config_dir="VectorConfig"):
        self.scene = scene_manager
        self.mode = mode
        self.config_dir = config_dir
        self.last_freqs = (None, None, None)
        self.load_mode_config(mode)

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
        print(f"[VectorClass] Načten režim '{mode}' z {config_path}")

        # Inicializace výchozích barev
        self.scene.set_color_for_group("bass", self.default_colors.get("bass", [255, 255, 255]))
        self.scene.set_color_for_group("midA", self.default_colors.get("midA", [255, 255, 255]))
        self.scene.set_color_for_group("midB", self.default_colors.get("midB", [255, 255, 255]))
        self.scene.set_color_for_group("midC", self.default_colors.get("midC", [255, 255, 255]))

    def process_audio_state(self, state):
        # Reakce na beat
        if state.beat_on_off:
            self.scene.pulse_on_beat("bass", intensity=255)

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
            if updated:
                self.visualize_state(state)
            self.last_freqs = freqs

    def visualize_state(self, state):
        def color_name(rgb):
            # Jednoduché převodní mapování pro zobrazení
            known_colors = {
                (255, 0, 0): "Red",
                (255, 127, 0): "Orange",
                (255, 255, 0): "Yellow",
                (0, 255, 0): "Green",
                (0, 255, 255): "Cyan",
                (0, 0, 255): "Blue",
                (255, 0, 255): "Magenta",
                (255, 255, 255): "White",
                (127, 127, 127): "Gray",
                (255, 105, 180): "Pink",
                (75, 0, 130): "Indigo",
                (139, 69, 19): "Brown",
            }
            return known_colors.get(tuple(rgb), str(rgb))

        freqs = state.freqs
        colors = [
            self.tone_colors.get(str(freqs[0]), [255, 255, 255]),
            self.tone_colors.get(str(freqs[1]), [255, 255, 255]),
            self.tone_colors.get(str(freqs[2]), [255, 255, 255]),
        ]

        print(f"[STATE] BEAT: {'✔' if state.beat_on_off else '✘'} | BPM: {state.bpm} | dB: {state.db:.1f} | FREQS: {freqs} | CHORD: {state.chord}")
        print(f"        COLORS → Bass+MidA: {color_name(colors[0])} | MidB: {color_name(colors[1])} | MidC: {color_name(colors[2])}\n")
