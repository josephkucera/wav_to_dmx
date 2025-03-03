import time
from pyftdi.ftdi import Ftdi
from LightPlot import LightPlot

class LightManager:
    """
    Spravuje DMX světla na základě načteného schématu osvětlení.
    """
    def __init__(self, light_file="light_plot.txt"):
        """
        Inicializuje FTDI kontrolér a načte světla ze souboru.
        """
        devices = list(Ftdi.list_devices())
        if not devices:
            raise RuntimeError("Žádné FTDI zařízení nenalezeno.")
        
        print("Nalezená zařízení:")
        for dev in devices:
            print(dev)
        
        first_device = devices[0][0]  # Získání prvního zařízení
        vid, pid = first_device.vid, first_device.pid  # Extrakce VID a PID
        
        self.ftdi = Ftdi()
        try:
            self.ftdi.open(vid, pid)
        except OSError as e:
            raise RuntimeError(f"Nepodařilo se otevřít FTDI zařízení: {e}")
        
        self.ftdi.set_baudrate(250000)
        self.ftdi.set_line_property(8, 2, 'N')
        
        self.dmx_data = [0] * 513  # DMX512 má 512 kanálů, index 0 je startovní kód
        self.light_plot = LightPlot(light_file)
        self.initialize_lights()
        
    def initialize_lights(self):
        """
        Inicializuje světla tak, že sníží všechny hodnoty větší než 0 o 1 (DMX adresy začínají od 1).
        """
        for light in self.light_plot.lights:
            for attr, value in light.__dict__.items():
                if isinstance(value, int) and value > 0:
                    setattr(light, attr, value - 1)
                else:
                    setattr(light, attr, None)
    
    def send_dmx_frame(self):
        """
        Odesílá DMX rámec do světelného systému.
        """
        self.ftdi.set_break(True)
        self.ftdi.set_break(False)
        self.ftdi.write_data(bytes(self.dmx_data))
    
    def set_light(self, light_type=None, param=None, value=0, value2=0, min_addr=0, max_addr=510):
        """
        Nastavuje hodnoty DMX kanálů pro daná světla.
        """
        for light in self.light_plot.lights:
            if light_type and not isinstance(light, globals().get(light_type, object)):
                continue
            if light.address is None or not (min_addr <= light.address <= max_addr):
                continue
            param_address = getattr(light, param, None)
            if param_address is not None:
                print(f"Nastavuji {param} na {value} pro světlo na adrese {light.address}")
                self.dmx_data[param_address] = value
                if value2:
                    print(f"Nastavuji {param} (16bit) na {value2} pro světlo na adrese {light.address}")
                    self.dmx_data[param_address + 1] = value2  # Pro 16bit parametry
        self.send_dmx_frame()
    
    def close(self):
        """
        Odpojí FTDI kontrolér a uvolní zdroje.
        """
        print("Odpojuji DMX kontrolér...")
        self.ftdi.close()

if __name__ == "__main__":
    manager = LightManager()
    
    # Zkušební nastavení světel
    manager.set_light(param="dim", value=255)  # Zapnutí všech světel na plný jas
    time.sleep(2)
    manager.set_light(param="dim", value=0)  # Zhasnutí všech světel
    
    # Odpojení DMX kontroléru
    manager.close()
