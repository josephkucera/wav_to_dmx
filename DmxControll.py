import time
import threading
from pyftdi.ftdi import Ftdi
from LightPlot import LightPlot

class LightManager:
    def __init__(self, light_file="light_plot.txt", dmx_frequency=40):
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
        
        self.dmx_data = [0] * 512
        self.light_plot = LightPlot(light_file)
        self.initialize_lights()
        
        self.running = True
        self.dmx_frequency = dmx_frequency
        self.dmx_thread = threading.Thread(target=self.dmx_loop, daemon=True)
        self.dmx_thread.start()
    
    def initialize_lights(self):
        for light in self.light_plot.lights:
            for attr, value in light.__dict__.items():
                if isinstance(value, int) and value > 0:
                    setattr(light, attr, value - 1)
                else:
                    setattr(light, attr, None)
    
    def dmx_loop(self):
        interval = 1 / self.dmx_frequency
        while self.running:
            self.ftdi.set_break(True)
            self.ftdi.set_break(False)
            self.ftdi.write_data(bytes(self.dmx_data))
            time.sleep(interval)
    
    def set_light(self, light_type=None, param=None, value=0, value2=0, min_addr=0, max_addr=510, fade=0):
        for light in self.light_plot.lights:
            if light_type and not isinstance(light, globals().get(light_type, object)):
                continue
            if light.address is None or not (min_addr <= light.address <= max_addr):
                continue
            param_address = getattr(light, param, None)
            if param_address is not None:
                if fade > 0:
                    threading.Thread(target=self.fade_light, args=(param_address + light.address, value, fade), daemon=True).start()
                    print(f"Nastavuji {param} na {value} pro světlo na adrese {light.address} s hodnotou fade {fade}")
                else:
                    print(f"Nastavuji {param} na {value} pro světlo na adrese {light.address}")
                    self.dmx_data[param_address + light.address] = value
                if value2:
                    self.dmx_data[param_address + light.address + 1] = value2
    
    def fade_light(self, address, target_value, fade_time):
        steps = max(1, int((fade_time / 1000) * self.dmx_frequency))
        start_value = self.dmx_data[address]
        step_value = (target_value - start_value) / steps if start_value != target_value else 0
        
        for i in range(steps):
            new_value = int(start_value + step_value * (i + 1))
            self.dmx_data[address] = max(0, min(255, new_value))
            time.sleep(1 / self.dmx_frequency)
    
    def close(self):
        print("Odpojuji DMX kontrolér...")
        self.running = False
        self.dmx_thread.join()
        self.ftdi.close()

if __name__ == "__main__":
    manager = LightManager()
    time.sleep(3)
    manager.set_light(light_type="par", param="dim", value=128, fade=0)
    manager.set_light(light_type="par", param="r", value=255, fade=2000)
    time.sleep(4)
    manager.set_light(light_type="par", param="g", value=255, fade=2000)
    manager.set_light(light_type="par", param="b", value=128, fade=500)
    manager.set_light(light_type="par", param="r", value=0, fade=3000)
    
    time.sleep(5)
    manager.set_light(light_type="par", param="dim", value=255, fade=2000)    
    manager.set_light(light_type="par", param="g", value=0, fade=2000)
    time.sleep(2)
    manager.set_light(light_type="par", param="b", value=255, fade=3000)
    time.sleep(3)
    manager.set_light(light_type="par", param="dim", value=0, fade=6000) 
    time.sleep(8)   
    manager.close()