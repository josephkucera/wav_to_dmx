import os
import json
import time
import threading
from pyftdi.ftdi import Ftdi
import math


class DMXController:
    """Udržuje DMX buffer a poskytuje metody pro práci s jednotlivými kanály."""
    def __init__(self):
        self.buffer = [0] * 512
        self.lock = threading.Lock()
        self.update = lambda: None  # Přepíše se zvenku, např. LightManagerem

    def set_value(self, address, value):
        if 0 <= address < 512:
            with self.lock:
                self.buffer[address] = max(0, min(255, value))

    def get_value(self, address):
        if 0 <= address < 512:
            with self.lock:
                return self.buffer[address]
        return 0


class Light:
    """Základní třída světla, sdílí jméno, adresu a přístup k DMX controlleru."""
    def __init__(self, name, address, dmx):
        self.name = name
        self.address = address
        self.dmx = dmx
        self._fade_threads = {}

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

    def _fade_single(self, addr, target, duration):
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
    def __init__(self, name, address, dim, dmx):
        super().__init__(name, address, dmx)
        self.dim = dim

    def set_dim(self, value, fade=0):
        self._fade_single(self.address, value, fade)
class Par(Light):
    def __init__(self, name, address, r, g, b, w, uv, dim, fade, strobo, dmx):
        super().__init__(name, address, dmx)
        self.r = r
        self.g = g
        self.b = b
        self.w = w
        self.uv = uv
        self.dim = dim
        self.fade = fade
        self.strobo = strobo

    def set_color(self, r, g, b, w=0, uv=0, fade=0):
        channels = [r, g, b, w, uv]
        for i, val in enumerate(channels):
            self._fade_single(self.address + i, val, fade)

    def set_dim(self, value, fade=0):
        self._fade_single(self.address + 5, value, fade)

    def set_strobe(self, value):
        self.dmx.set_value(self.address + 7, value)


class Head(Par):
    def __init__(self, name, address, r, g, b, w, uv, dim, fade, strobo, pan, panF, tilt, tiltF, speed, zoom, dmx):
        super().__init__(name, address, r, g, b, w, uv, dim, fade, strobo, dmx)
        self.pan = pan
        self.panF = panF
        self.tilt = tilt
        self.tiltF = tiltF
        self.speed = speed
        self.zoom = zoom

    def set_position(self, pan, tilt, fade=0):
        self._fade_single(self.address + 8, pan, fade)
        self._fade_single(self.address + 10, tilt, fade)

    def set_movement_speed(self, speed):
        self.dmx.set_value(self.address + 12, speed)

    def set_zoom(self, zoom):
        self.dmx.set_value(self.address + 13, zoom)


class Haze(Light):
    def __init__(self, name, address, haze, fan, dmx):
        super().__init__(name, address, dmx)
        self.haze = haze
        self.fan = fan

    def set_haze(self, value):
        self.dmx.set_value(self.address, value)

    def set_fan(self, value):
        self.dmx.set_value(self.address + 1, value)


class LightPlot:
    def __init__(self, filename, dmx):
        self.filename = filename
        self.lights = []
        self.dmx = dmx
        self.load_lights()

    def load_lights(self):
        if not os.path.exists(self.filename):
            print("Soubor nenalezen, vytvářím nový se vzorovým světlem.")
            self.lights.append(Head("Univerzal", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, dmx=self.dmx))
            self.save_lights()
        else:
            with open(self.filename, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue  # ⬅️ přeskočíme prázdný řádek
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
        print("Nalezená zařízení:")
        for dev in devices:
            print(dev)
        first_device = devices[0][0]
        vid, pid = first_device.vid, first_device.pid

        self.ftdi = Ftdi()
        try:
            self.ftdi.open(vid, pid)
        except OSError as e:
            raise RuntimeError(f"Nepodařilo se otevřít FTDI zařízení: {e}")

        self.ftdi.set_baudrate(250000)
        self.ftdi.set_line_property(8, 2, 'N')

        self.dmx = DMXController()
        self.dmx.update = self._send_dmx_data

        self.light_plot = LightPlot(light_file, self.dmx)

        self.running = True
        self.dmx_frequency = dmx_frequency
        self.dmx_thread = threading.Thread(target=self.dmx_loop, daemon=True)
        self.dmx_thread.start()

        print("DMX smyčka spuštěna...")

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
        print("Odpojuji DMX kontrolér...")
        self.running = False
        self.dmx_thread.join()
        self.ftdi.close()
        

class SceneManager:
    def __init__(self, light_plot):
        self.light_plot = light_plot
        # Rozdělení světel do kategorií podle DMX adres
        self.ranges = {
            "bass": (0, 61),
            "mid": (61, 151),
            "high": (151, 231)
        }

    def get_lights_in_range(self, start, end):
        return [light for light in self.light_plot.lights if start <= light.address < end]

    def get_group_lights(self, group_name):
        if group_name in self.ranges:
            start, end = self.ranges[group_name]
            return self.get_lights_in_range(start, end)
        return []

    def blackout(self, fade=0.5):
        for light in self.light_plot.lights:
            if hasattr(light, 'set_dim'):
                light.set_dim(0, fade=fade)

    def set_color_for_group(self, group, color, fade=1.0):
        r, g, b = color
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_color'):
                light.set_color(r, g, b, fade=fade)

    def set_dim_for_group(self, group, value, fade=1.0):
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_dim'):
                light.set_dim(value, fade=fade)

    def pulse_on_beat(self, group, intensity=255, fade=0.2):
        """Rozsvítí světla v dané skupině na momentální beat a pak zhasne."""
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_dim'):
                light.set_dim(intensity, fade=fade)
        time.sleep(fade)
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_dim'):
                light.set_dim(0, fade=fade)

    def gradient_across_group(self, group, colors, fade=1.0):
        """Barevný gradient podle adresy – přechází mezi barvami zleva doprava."""
        lights = self.get_group_lights(group)
        count = len(lights)
        if count == 0 or len(colors) < 2:
            return

        for i, light in enumerate(lights):
            ratio = i / (count - 1) if count > 1 else 0
            index = ratio * (len(colors) - 1)
            low = int(index)
            high = min(low + 1, len(colors) - 1)
            t = index - low
            r = int(colors[low][0] * (1 - t) + colors[high][0] * t)
            g = int(colors[low][1] * (1 - t) + colors[high][1] * t)
            b = int(colors[low][2] * (1 - t) + colors[high][2] * t)
            if hasattr(light, 'set_color'):
                light.set_color(r, g, b, fade=fade)

    def set_position_for_group(self, group, pan, tilt, fade=1.0):
        """Nastaví všem hlavám ve skupině pozici."""
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_position'):
                light.set_position(pan, tilt, fade=fade)

    def offset_position_for_group(self, group, pan_offset=0, tilt_offset=0, fade=1.0):
        """Uhne všem hlavám od jejich aktuální základní pozice."""
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_position') and hasattr(light, 'pan') and hasattr(light, 'tilt'):
                target_pan = light.pan + pan_offset
                target_tilt = light.tilt + tilt_offset
                light.set_position(target_pan, target_tilt, fade=fade)

    def set_zoom_for_group(self, group, value):
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_zoom'):
                light.set_zoom(value)

    def set_speed_for_group(self, group, value):
        for light in self.get_group_lights(group):
            if hasattr(light, 'set_movement_speed'):
                light.set_movement_speed(value)
                
    def set_dim_all(self, value, fade=1.0):
        for group in self.ranges.keys():
            self.set_dim_for_group(group, value, fade=fade)


    def wave_motion(self, group="high", pan=127, tilt_amplitude=40, steps=6, fade=1.0, delay=0.4):
        """Simuluje vlnu pomocí různého tilt úhlu pro každou hlavu ve skupině."""
        heads = [light for light in self.get_group_lights(group) if hasattr(light, 'set_position')]
        count = len(heads)

        for step in range(steps):
            for i, light in enumerate(heads):
                angle = math.sin((step + i / count) * math.pi * 2 / steps)
                tilt = int(127 + angle * tilt_amplitude)
                light.set_position(pan, tilt, fade=fade)
            time.sleep(delay)


class SimulatorManager:
    """Simuluje DMX komunikaci bez FTDI zařízení – ideální pro testování."""
    def __init__(self, light_file="light_plot.txt", dmx_frequency=1):
        self.dmx = DMXController()
        self.dmx.update = self._simulate_dmx_output

        self.light_plot = LightPlot(light_file, self.dmx)

        self.running = True
        self.dmx_frequency = dmx_frequency
        self.dmx_thread = threading.Thread(target=self.dmx_loop, daemon=True)
        self.dmx_thread.start()

        print("Simulátor DMX spuštěn...")

    def _simulate_dmx_output(self):
        # Vypíše hodnoty v bufferu, kde došlo ke změně
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

    def set_all_color(light_plot, r, g, b, fade=1.0):
        for light in light_plot.lights:
            if isinstance(light, Par):
                light.set_color(r, g, b, fade=fade)

import time

if __name__ == "__main__":
    manager = None
    try:

        manager = SimulatorManager("light_plot.txt", dmx_frequency=2)
        scenes = SceneManager(manager.light_plot)

        print("Zapínám všechna světla...")
        scenes.set_dim_all(255, fade=1.0)

        print("Nastavuji barvy podle skupin...")
        scenes.set_color_for_group("bass", (255, 0, 0), fade=1.0)   # červená
        scenes.set_color_for_group("mid", (0, 0, 255), fade=1.0)    # modrá
        scenes.set_color_for_group("high", (0, 255, 0), fade=1.0)   # zelená
        time.sleep(3)

        print("Pulz na beat pro BASS...")
        scenes.pulse_on_beat("bass", intensity=255, fade=0.3)
        time.sleep(1)

        print("Gradient across MID...")
        scenes.gradient_across_group("mid", [(255, 0, 0), (0, 0, 255)], fade=1.0)
        time.sleep(3)

        print("Pohyb hlav do základní pozice...")
        scenes.set_position_for_group("high", pan=127, tilt=127, fade=1.0)
        time.sleep(1)

        print("Vlnový pohyb hlav...")
        scenes.wave_motion(group="high", pan=127, tilt_amplitude=40, steps=8, fade=0.5, delay=0.3)

        print("Zoom a speed...")
        scenes.set_zoom_for_group("high", 200)
        scenes.set_speed_for_group("high", 180)
        time.sleep(2)

        print("Blackout všech světel...")
        scenes.blackout(fade=2.0)

        input("Stiskněte Enter pro ukončení...")

    finally:
        if manager:
            manager.cleanup()

