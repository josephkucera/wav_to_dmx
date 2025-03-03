import pandas as pd

class LightManager:
    def __init__(self, filename="light_plot.xlsx"):
        self.filename = filename
        self.lights = []
        self.load_lights()
    
    def load_lights(self):
        """Načte seznam světel ze souboru"""
        try:
            df = pd.read_excel(self.filename)
            self.lights = df.to_dict(orient="records")
        except FileNotFoundError:
            self.lights = []
    
    def save_lights(self):
        """Uloží seznam světel do souboru"""
        df = pd.DataFrame(self.lights)
        df.to_excel(self.filename, index=False)
    
    def add_light(self, name, light_type, start_address, **params):
        """Přidá nové světlo do seznamu"""
        light = {"name": name, "type": light_type, "start_address": start_address, **params}
        self.lights.append(light)
        self.save_lights()
    
    def get_lights_by_type(self, light_type):
        """Vrátí seznam světel určitého typu"""
        return [light for light in self.lights if light["type"] == light_type]
    
    def get_lights_in_range(self, start, end):
        """Vrátí světla v určitém rozsahu DMX adres"""
        return [light for light in self.lights if start <= light["start_address"] <= end]

# Příklad použití
if __name__ == "__main__":
    manager = LightManager()
    manager.add_light("Universal", "head", 10, r=0, g=0, b=0, w=0, uv=0, dim=0, fade=0, strobo=0, pan=0, panF=0, tilt=0, tiltF=0, speed=0, zoom=0)
    manager.add_light("par64", "par", 10, r=1, g=2, b=3, w=0, dim=4, fade=5, strobo=6)
    manager.add_light("headEurolite", "head", 30, r=8, g=9, b=10, w=11, dim=0, pan=6, tilt=14)
    print(manager.get_lights_by_type("par"))
    print(manager.get_lights_in_range(0, 100))