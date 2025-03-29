import time
import threading
from pyftdi.ftdi import Ftdi
from LightPlot import LightPlot

class LightManager:
    """
    Tato třída je určená pro komunikaci se DMX převodníkem a třídou LightPlot které načítá světla ze souboru a upravuje je
    -
    __innit__ připojí ftdi zařízení, vytovří DMX buffer a spustí DMX smyčku, Zároveň inicializuje světla ze souboru
    Metoda set_fixture pro nastavení konkrétních světel v nějakém rozsahu na danou hodnotu.
    """
    def __init__(self, light_file="light_plot.txt", dmx_frequency=40):
        # Získání seznamu připojených FTDI zařízení (DMX převodníků)
        devices = list(Ftdi.list_devices())
        if not devices:
            raise RuntimeError("Žádné FTDI zařízení nenalezeno.")  # Pokud není žádné zařízení, ukončí se program
        
        # Výpis nalezených zařízení
        print("Nalezená zařízení:")
        for dev in devices:
            print(dev)
        
        # Použití prvního nalezeného zařízení
        first_device = devices[0][0]
        vid, pid = first_device.vid, first_device.pid
        
        # Inicializace FTDI zařízení
        self.ftdi = Ftdi()
        try:
            self.ftdi.open(vid, pid)
        except OSError as e:
            raise RuntimeError(f"Nepodařilo se otevřít FTDI zařízení: {e}")
        
        # Nastavení DMX komunikace
        self.ftdi.set_baudrate(250000)  # Standardní baudrate pro DMX
        self.ftdi.set_line_property(8, 2, 'N')  # 8 datových bitů, 2 stop bity, žádná parita
        
        # Inicializace DMX bufferu (512 kanálů)
        self.dmx_data = [0] * 512
        
        # Načtení světel ze souboru
        self.light_plot = LightPlot(light_file)
        self.initialize_lights()  # Převod adres na indexy

        # Spuštění DMX smyčky
        self.running = True
        self.dmx_frequency = dmx_frequency
        self.dmx_thread = threading.Thread(target=self.dmx_loop, daemon=True)
        self.dmx_thread.start()
    
    def initialize_lights(self):
        """Inicializuje adresy světel tak, aby odpovídaly indexům v DMX bufferu."""
        for light in self.light_plot.lights:
            for attr, value in light.__dict__.items():
                if isinstance(value, int) and value > 0:
                    setattr(light, attr, value - 1)  # DMX adresy se indexují od 0
                else:
                    setattr(light, attr, None)  # Neplatné hodnoty jsou nastaveny na None
    
    def dmx_loop(self):
        """Nekonečná smyčka pro odesílání DMX dat."""
        interval = 1 / self.dmx_frequency
        while self.running:
            self.ftdi.set_break(True)  # DMX Start Code (Break)
            self.ftdi.set_break(False)
            self.ftdi.write_data(bytes(self.dmx_data))  # Odeslání DMX bufferu
            time.sleep(interval)  # Počkání na další iteraci
    
    def set_fixture(self, light_type=None, param=None, value=0, value2=0, min_addr=0, max_addr=510, fade=1000):
        """
        Nastavuje hodnoty DMX kanálů pro určitý typ světla.
        - light_type: typ světla (např. "par")
        - param: parametr světla (např. "dim", "r", "g", "b")
        - value: hlavní hodnota parametru
        - value2: druhá hodnota (pro 16bit nastavení)
        - min_addr, max_addr: rozsah adres světel
        - fade: doba přechodu na novou hodnotu
        """
        for light in self.light_plot.lights:
            # Ověření, zda odpovídá zadanému typu
            if light_type and not isinstance(light, globals().get(light_type, object)):
                continue
            # Kontrola, zda je světlo v požadovaném rozsahu adres
            if light.address is None or not (min_addr <= light.address <= max_addr):
                continue
            # Získání adresy parametru
            param_address = getattr(light, param, None)
            if param_address is not None:
                if fade > 0:
                    threading.Thread(target=self.fade_light, args=(param_address + light.address, value, fade), daemon=True).start()
                    print(f"Nastavuji {param} na {value} pro světlo na adrese {light.address} s hodnotou fade {fade}")
                else:
                    print(f"Nastavuji {param} na {value} pro světlo na adrese {light.address}")
                    self.dmx_data[param_address + light.address] = value  # Okamžitá změna hodnoty
                if value2:
                    self.dmx_data[param_address + light.address + 1] = value2  # Pokud je třeba nastavit i druhý DMX kanál
    
    def fade_light(self, address, target_value, fade_time):
        """
        Plynule mění hodnotu DMX kanálu na cílovou hodnotu v daném čase.
        - address: adresa DMX kanálu
        - target_value: konečná hodnota
        - fade_time: doba změny (v ms)
        """
        steps = max(1, int((fade_time / 1000) * self.dmx_frequency))  # Počet kroků přechodu
        start_value = self.dmx_data[address]
        step_value = (target_value - start_value) / steps if start_value != target_value else 0
        
        for i in range(steps):
            new_value = int(start_value + step_value * (i + 1))
            self.dmx_data[address] = max(0, min(255, new_value))  # Ochrana proti přetečení
            time.sleep(1 / self.dmx_frequency)  # Počkání mezi kroky přechodu
    
    def close(self):
        """Zastaví DMX smyčku a zavře FTDI zařízení."""
        print("Odpojuji DMX kontrolér...")
        self.running = False
        self.dmx_thread.join()  # Počkání na ukončení DMX smyčky
        self.ftdi.close()  # Zavření komunikace

if __name__ == "__main__":
    # Testovací sekvence nastavení světel
    manager = LightManager()
    time.sleep(3)
    manager.set_fixture(light_type="par", param="dim", value=128, fade=0)
    manager.set_fixture(light_type="par", param="r", value=255, fade=2000)
    time.sleep(4)
    manager.set_fixture(light_type="par", param="g", value=255, fade=2000)
    manager.set_fixture(light_type="par", param="b", value=128, fade=500)
    manager.set_fixture(light_type="par", param="r", value=0, fade=3000)
    
    time.sleep(5)
    manager.set_fixture(light_type="par", param="dim", value=255, fade=2000)    
    manager.set_fixture(light_type="par", param="g", value=0, fade=2000)
    time.sleep(2)
    manager.set_fixture(light_type="par", param="b", value=255, fade=3000)
    time.sleep(3)
    manager.set_fixture(light_type="par", param="dim", value=0, fade=6000) 
    time.sleep(8)   
    manager.close()  # Ukončení programu
