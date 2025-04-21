import os
import json
import time
import threading
from pyftdi.ftdi import Ftdi
from IPython import embed


class DMXController:
    def __init__(self):
        self.buffer = [0] * 512
        self.lock = threading.Lock()

    def set_value(self, address, value):
        if 0 <= address < 512:
            with self.lock:
                self.buffer[address] = max(0, min(255, value))

    def get_value(self, address):
        if 0 <= address < 512:
            with self.lock:
                return self.buffer[address]
        return 0

    def update(self):
        pass


class Light:
    """Základní třída světla, sdílí jméno, adresu a přístup k DMX controlleru."""
    def __init__(self, name, address, dmx):
        self.name = name
        self.address = address
        self.dmx = dmx
        self._fade_threads = {}
        self.channels = {}  # Mapování parametrů (např. 'r', 'g', 'pan') na adresy

    def __str__(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_dict(self):
        data = {**self.__dict__, "type": type(self).__name__.lower()}
        data.pop("dmx", None)
        data.pop("_fade_threads", None)
        return data

    @staticmethod
    def from_dict(data, dmx):
        light_type = data.pop("type")
        light_classes = {
            "dimr": Dimr,
            "par": Par,
            "head": Head,
            "haze": Haze
        }
        return light_classes[light_type](dmx=dmx, **data)

    def init_channels(self, data):
        """Inicializuje mapu kanálů podle offsetů v načtených datech."""
        for param, offset in data.items():
            if isinstance(offset, int) and offset > 0:
                self.channels[param] = self.address + (offset - 1)

    def set_param(self, param, value):
        """Nastaví daný parametr světla na hodnotu pomocí interpolace."""
        if param in self.channels:
            addr = self.channels[param]
            self._fade_single(addr, value)

    def _fade_single(self, addr, target, duration=0.5):
        if addr in self._fade_threads:
            self._fade_threads[addr].set()

        stop_event = threading.Event()
        self._fade_threads[addr] = stop_event

        def interpolator():
            start = self.dmx.get_value(addr)
            steps = max(1, int(duration / 0.05))
            for i in range(steps):
                if stop_event.is_set():
                    return
                val = int(start + (target - start) * (i + 1) / steps)
                self.dmx.set_value(addr, val)
                time.sleep(0.05)
            self.dmx.set_value(addr, target)

        threading.Thread(target=interpolator, daemon=True).start()


class Dimr(Light):
    def __init__(self, name, address, dmx, **kwargs):
        super().__init__(name, address, dmx)
        self.init_channels(kwargs)

    def set_dim(self, value):
        self.set_param("dim", value)


class Par(Light):
    def __init__(self, name, address, dmx, **kwargs):
        super().__init__(name, address, dmx)
        self.init_channels(kwargs)

    def set_color(self, r=0, g=0, b=0, w=0, uv=0):
        for param, val in zip(["r", "g", "b", "w", "uv"], [r, g, b, w, uv]):
            self.set_param(param, val)

    def set_dim(self, value):
        self.set_param("dim", value)

    def set_strobe(self, value):
        self.set_param("strobo", value)


class Head(Par):
    def __init__(self, name, address, dmx, base_pan=127, base_tilt=127, **kwargs):
        super().__init__(name, address, dmx, **kwargs)
        self.base_pan = base_pan
        self.base_tilt = base_tilt

    def set_position(self, pan, tilt):
        self.set_param("pan", pan)
        self.set_param("tilt", tilt)

    def set_movement_speed(self, value):
        self.set_param("speed", value)

    def set_zoom(self, value):
        self.set_param("zoom", value)


class Haze(Light):
    def __init__(self, name, address, dmx, **kwargs):
        super().__init__(name, address, dmx)
        self.init_channels(kwargs)

    def set_haze(self, value):
        self.set_param("haze", value)

    def set_fan(self, value):
        self.set_param("fan", value)



class LightPlot:
    def __init__(self, filename, dmx):
        self.filename = filename
        self.lights = []
        self.dmx = dmx
        self.load_lights()

    def load_lights(self):
        if not os.path.exists(self.filename):
            print("Soubor nenalezen, vytvářím nový se vzorovým světlem.")
            return
        with open(self.filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                self.lights.append(Light.from_dict(data, self.dmx))

    def save_lights(self):
        with open(self.filename, "w", encoding="utf-8") as file:
            for light in self.lights:
                file.write(json.dumps(light.to_dict(), ensure_ascii=False) + "\n")

    def add_light(self, light):
        self.lights.append(light)
        self.save_lights()

    def remove_light(self, index):
        if 0 <= index < len(self.lights):
            removed_light = self.lights.pop(index)
            self.save_lights()
            return removed_light
        return None

    def list_lights(self):
        for light in self.lights:
            print(light)


class LightManager:
    def __init__(self, light_file="light_plot.txt", dmx_frequency=45):
        devices = list(Ftdi.list_devices())
        if not devices:
            raise RuntimeError("Žádné FTDI zařízení nenalezeno.")
        first_device = devices[0][0]
        vid, pid = first_device.vid, first_device.pid

        self.ftdi = Ftdi()
        self.ftdi.open(vid, pid)
        self.ftdi.set_baudrate(250000)
        self.ftdi.set_line_property(8, 2, 'N')

        self.dmx = DMXController()
        self.dmx.update = self._send_dmx_data
        self.light_plot = LightPlot(light_file, self.dmx)

        self.running = True
        self.dmx_frequency = dmx_frequency
        self.dmx_thread = threading.Thread(target=self.dmx_loop, daemon=True)
        self.dmx_thread.start()
        print("DMX Připojeno...")

    def _send_dmx_data(self):
        self.ftdi.set_break(True)
        self.ftdi.set_break(False)
        self.ftdi.write_data(bytes(self.dmx.buffer))

    def dmx_loop(self):
        interval = 1 / self.dmx_frequency
        while self.running:
            self.dmx.update()
            time.sleep(interval)

    def cleanup(self):
        self.running = False
        self.dmx_thread.join()
        self.ftdi.close()


class SimulatorManager:
    def __init__(self, light_file="light_plot.txt", dmx_frequency=2):
        self.dmx = DMXController()
        self.dmx.update = self._simulate_dmx_output
        self.light_plot = LightPlot(light_file, self.dmx)
        self.running = True
        self.dmx_frequency = dmx_frequency
        self.dmx_thread = threading.Thread(target=self.dmx_loop, daemon=True)
        self.dmx_thread.start()
        print("Simulátor DMX spuštěn...")

    def _simulate_dmx_output(self):
        active_channels = [(i, val) for i, val in enumerate(self.dmx.buffer) if val > 0]
        if active_channels:
            print("Aktivní kanály:")
            for addr, val in active_channels:
                print(f"  Kanál {addr+1}: {val}")
            print("-----")

    def dmx_loop(self):
        interval = 1 / self.dmx_frequency
        while self.running:
            self.dmx.update()
            time.sleep(interval)

    def cleanup(self):
        print("Ukončuji DMX simulátor...")
        self.running = False
        self.dmx_thread.join()


class SceneManager:
    def __init__(self, light_plot):
        self.light_plot = light_plot
        self.ranges = {
            "bass": (2, 61),
            "midA": (61, 81),
            "midB": (81, 121),
            "midC": (121, 161),
            "highA": (161, 196),
            "highB": (196, 231),
            "special":(0,1)
        }

    def get_lights_in_range(self, start, end):
        return [light for light in self.light_plot.lights if start <= light.address < end]

    def get_group_lights(self, group_name):
        if group_name in self.ranges:
            start, end = self.ranges[group_name]
            return self.get_lights_in_range(start, end)
        return []

    def blackout(self):
        for light in self.light_plot.lights:
            if hasattr(light, 'set_dim'):
                light.set_dim(0)
        print("provadim zhasnuti svetel")

    def set_color_for_group(self, group, color):
        """
        Nastaví barvu světel ve skupině. Podporuje RGB a volitelně W a UV.
        Parametr `color` může být (r, g, b), (r, g, b, w) nebo (r, g, b, w, uv)
        """
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_color'):
                r, g, b = color[0], color[1], color[2]
                w = color[3] if len(color) > 3 else 0
                uv = color[4] if len(color) > 4 else 0

                supports_w = "w" in getattr(light, "channels", {})
                supports_uv = "uv" in getattr(light, "channels", {})

                light.set_color(
                    r, g, b,
                    w=w if supports_w else 0,
                    uv=uv if supports_uv else 0
                )

    def set_dim_for_group(self, group, value):
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_dim'):
                light.set_dim(value)

    def pulse_on_beat(self, group, intensity=255, duration=0.2):
        def pulse_thread():
            time.sleep(0.03)  # malá pauza před nastavením
            for light in self.get_group_lights(group):
                if hasattr(light, 'set_dim'):
                    light.set_dim(intensity)
            time.sleep(duration)
            for light in self.get_group_lights(group):
                if hasattr(light, 'set_dim'):
                    light.set_dim(128)

        threading.Thread(target=pulse_thread, daemon=True).start()

    def set_zoom_for_group(self, group, value):
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_zoom'):
                light.set_zoom(value)

    def set_movement_for_group(self, group, pan=None, tilt=None, speed=None):
        """
        Nastaví pozici a/nebo rychlost pohybu světel ve skupině.
        Automaticky použije i 16bit verzi (panF, tiltF), pokud ji světlo má.
        """
        for light in self.get_group_lights(group):
            # Nastavení pozice
            if pan is not None or tilt is not None:
                if hasattr(light, "channels"):
                    if pan is not None and "pan" in light.channels:
                        light.set_param("pan", pan)
                        if "panF" in light.channels:
                            light.set_param("panF", 0)  # nebo jemná hodnota dle potřeby
                    if tilt is not None and "tilt" in light.channels:
                        light.set_param("tilt", tilt)
                        if "tiltF" in light.channels:
                            light.set_param("tiltF", 0)  # nebo jemná hodnota dle potřeby

            # Nastavení rychlosti
            if speed is not None and hasattr(light, "set_movement_speed"):
                light.set_movement_speed(speed)

    def set_dim_all(self, value):
        for group in self.ranges.keys():
            self.set_dim_for_group(group, value)



if __name__ == "__main__":
    manager = LightManager("light_plot.txt", dmx_frequency=30)
    scenes = SceneManager(manager.light_plot)

    print("Spouštím IPython interaktivní shell...")
    embed(header="""
    Vítej v interaktivním shellu!
    Příklady:
    scenes.set_dim_all(255)       # zapne všechna světla
    scenes.blackout()             # vypne všechna světla
    scenes.pulse_on_beat('bass')  # pulz pro skupinu bass
    scenes.set_color_for_group("bass", (255, 255, 255)) # nastaví bílou na bass
    Vypnutí je pomocí Ctrl + D 
        """)


    manager.cleanup()

# if __name__ == "__main__":
#     manager = LightManager("light_plot.txt", dmx_frequency=30)
#     scenes = SceneManager(manager.light_plot)

#     print("Zkouška: Bílá barva + plný dimmer")
#     scenes.set_color_for_group("bass", (255, 255, 255))
#     scenes.set_dim_for_group("bass", 255)

#     time.sleep(3)

#     print("Snížení dimmeru na 0...")
#     scenes.set_dim_for_group("bass", 0)

#     time.sleep(2)
#     print("Test ukončen")
#     manager.cleanup()