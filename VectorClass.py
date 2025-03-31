import json
import os

class VectorClass:
    def __init__(self, scene_manager, mode_file="VectorConfig/default.json"):
        self.scene = scene_manager
        self.initialized = False
        self.mode_file = mode_file

        # Výchozí hodnoty pokud se JSON nepodaří načíst
        self.default_colors = {
            "bass": (255, 255, 255),  # bílá
            "midA": (255, 0, 0),      # červená
            "midB": (0, 255, 0),      # zelená
            "midC": (0, 0, 255),      # modrá
        }

        self.tone_colors = {
            0: (255, 255, 255),
            1: (255, 0, 0),
            2: (255, 127, 0),
            3: (255, 255, 0),
            4: (0, 255, 0),
            5: (0, 255, 255),
            6: (0, 127, 255),
            7: (0, 0, 255),
            8: (127, 0, 255),
            9: (255, 0, 255),
            10: (255, 0, 127),
            11: (127, 127, 127),
        }

        self.last_freqs = (None, None, None)
        self.load_mode(self.mode_file)

    def load_mode(self, filepath):
        if not os.path.exists(filepath):
            print(f"[VectorClass] Konfigurační soubor {filepath} nenalezen. Používám výchozí hodnoty.")
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.default_colors = data.get("default_colors", self.default_colors)
                self.tone_colors = {int(k): tuple(v) for k, v in data.get("tone_colors", self.tone_colors).items()}
                print(f"[VectorClass] Načten režim z {filepath}")
        except Exception as e:
            print(f"[VectorClass] Chyba při načítání režimu: {e}")

    def update(self, state):
        # Inicializace scén po startu
        if not self.initialized:
            for group, color in self.default_colors.items():
                self.scene.set_dim_for_group(group, 127)
                self.scene.set_color_for_group(group, color)
            self.initialized = True

        # Pulse on beat
        if state.beat_on_off:
            self.scene.pulse_on_beat("bass", intensity=255)

        # Nastavení barev podle frekvencí (pouze při změně)
        freqs = state.freqs
        if len(freqs) >= 3:
            if freqs[0] != self.last_freqs[0]:
                self.scene.set_color_for_group("bass", self.tone_colors.get(freqs[0], (255, 255, 255)))
                self.scene.set_color_for_group("midA", self.tone_colors.get(freqs[0], (255, 255, 255)))
            if freqs[1] != self.last_freqs[1]:
                self.scene.set_color_for_group("midB", self.tone_colors.get(freqs[1], (255, 255, 255)))
            if freqs[2] != self.last_freqs[2]:
                self.scene.set_color_for_group("midC", self.tone_colors.get(freqs[2], (255, 255, 255)))
            self.last_freqs = freqs
