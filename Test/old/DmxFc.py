import Test.DmxControll as d
import time

class DmxManager:
    def __init__(self, dmx):
        # Nastavení objektu DMX
        self.dmx = dmx

    def close(self):
        self.dmx.close()  # Správné zavření instance
        
    def blackout(self):
        self.dmx.set_fixture(light_type="par", param="dim", value=0)
        self.dmx.set_fixture(light_type="dimr", param="dim", value=0)
        self.dmx.set_fixture(light_type="head", param="dim", value=0)

    def all_lights_half(self):
        self.dmx.set_fixture(light_type="par", param="dim", value=127)
        self.dmx.set_fixture(light_type="dimr", param="dim", value=127)
        self.dmx.set_fixture(light_type="head", param="dim", value=127)
    
    def all_lights_full(self):
        self.dmx.set_fixture(light_type="par", param="dim", value=255)
        self.dmx.set_fixture(light_type="dimr", param="dim", value=255)
        self.dmx.set_fixture(light_type="head", param="dim", value=255)
    
    def set_lights_red(self, min_addr=0, max_addr=510):
        self.dmx.set_fixture(light_type="par", param="r", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="r", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="g", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="g", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="b", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="b", value=0, min_addr=min_addr, max_addr=max_addr)
    
    def set_lights_green(self, min_addr=0, max_addr=510):
        self.dmx.set_fixture(light_type="par", param="r", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="r", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="g", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="g", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="b", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="b", value=0, min_addr=min_addr, max_addr=max_addr)
        
    def set_lights_blue(self, min_addr=0, max_addr=510):
        self.dmx.set_fixture(light_type="par", param="r", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="r", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="g", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="g", value=0, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="b", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="b", value=255, min_addr=min_addr, max_addr=max_addr)
        
    def set_lights_white(self, min_addr=0, max_addr=510):
        self.dmx.set_fixture(light_type="par", param="r", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="r", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="g", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="g", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="par", param="b", value=255, min_addr=min_addr, max_addr=max_addr)
        self.dmx.set_fixture(light_type="head", param="b", value=255, min_addr=min_addr, max_addr=max_addr)
    
    def reset_heads(self):
        self.dmx.set_fixture(light_type="head", param="pan", value=127)
        self.dmx.set_fixture(light_type="head", param="tilt", value=127)
    
    def beat_effect(self):
        self.dmx.set_fixture(light_type="par", max_addr=100, param="dim", value=255, fade=100)
        self.dmx.set_fixture(light_type="dimr", max_addr=100, param="dim", value=255, fade=100)
        self.dmx.set_fixture(light_type="head", max_addr=100, param="dim", value=255, fade=100)
        time.sleep(0.4)
        self.dmx.set_fixture(light_type="par", max_addr=100, param="dim", value=80, fade=400)
        self.dmx.set_fixture(light_type="dimr", max_addr=100, param="dim", value=80, fade=400)
        self.dmx.set_fixture(light_type="head", max_addr=100, param="dim", value=80, fade=400)
        time.sleep(0.4)

if __name__ == "__main__":
    dmx = d.LightManager()  # Vytvoření instance DMX kontroleru
    manager = DmxManager(dmx)  # Předání do DmxManager
    
    manager.all_lights_half()
    time.sleep(2)
    manager.set_lights_red()
    time.sleep(2)
    manager.set_lights_green()
    time.sleep(2)
    manager.set_lights_blue()
    time.sleep(2)
    manager.set_lights_white()
    time.sleep(2)
    
    for i in range(10):
        manager.beat_effect()
    
    manager.blackout()
    time.sleep(2)

    manager.close()  # Ukončení programu správným zavřením DMX
