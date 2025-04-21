import os
import json

class Light:
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

class Dimr(Light):
    def __init__(self, name, address, dim):
        super().__init__(name, address)
        self.dim = dim

class Par(Light):
    def __init__(self, name, address, r, g, b, w, uv, dim, fade, strobo):
        super().__init__(name, address)
        self.r = r
        self.g = g
        self.b = b
        self.w = w
        self.uv = uv
        self.dim = dim
        self.fade = fade
        self.strobo = strobo

class Head(Light):
    def __init__(self, name, address, r, g, b, w, uv, dim, fade, strobo,
                 pan, panF, tilt, tiltF, speed, zoom, base_pan=127, base_tilt=127):
        super().__init__(name, address)
        self.r = r
        self.g = g
        self.b = b
        self.w = w
        self.uv = uv
        self.dim = dim
        self.fade = fade
        self.strobo = strobo
        self.pan = pan
        self.panF = panF
        self.tilt = tilt
        self.tiltF = tiltF
        self.speed = speed
        self.zoom = zoom
        self.base_pan = base_pan
        self.base_tilt = base_tilt

class Haze(Light):
    def __init__(self, name, address, haze, fan):
        super().__init__(name, address)
        self.haze = haze
        self.fan = fan

class LightPlot:
    def __init__(self, filename):
        self.filename = filename
        self.lights = []
        self.load_lights()

    def load_lights(self):
        self.lights.clear()
        if not os.path.exists(self.filename):
            print("Soubor nenalezen, vytvářím nový se vzorovým světlem.")
            self.lights.append(Head("Univerzal", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 127, 127))
            self.save_lights()
        else:
            with open(self.filename, "r", encoding="utf-8") as file:
                for line in file:
                    data = json.loads(line.strip())
                    light_type = data.pop("type")
                    if light_type == "dimr":
                        self.lights.append(Dimr(**data))
                    elif light_type == "par":
                        self.lights.append(Par(**data))
                    elif light_type == "head":
                        self.lights.append(Head(**data))
                    elif light_type == "haze":
                        self.lights.append(Haze(**data))

    def save_lights(self):
        with open(self.filename, "w", encoding="utf-8") as file:
            for light in self.lights:
                data = {**light.__dict__, "type": type(light).__name__.lower()}
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

    def add_light(self):
        print("Dostupné typy světel: dimr, par, head, haze")
        light_type = input("Vyberte typ světla: ").strip().lower()
        name = input("Zadejte název: ")
        address = int(input("Zadejte adresu: "))

        if light_type == "dimr":
            dim = int(input("Zadejte hodnotu dim: "))
            light = Dimr(name, address, dim)
        elif light_type == "par":
            params = [int(input(f"Zadejte hodnotu {param}: ")) for param in
                      ["r", "g", "b", "w", "uv", "dim", "fade", "strobo"]]
            light = Par(name, address, *params)
        elif light_type == "head":
            params = [int(input(f"Zadejte hodnotu {param}: ")) for param in
                      ["r", "g", "b", "w", "uv", "dim", "fade", "strobo",
                       "pan", "panF", "tilt", "tiltF", "speed", "zoom"]]
            base_pan = int(input("Zadejte výchozí hodnotu base_pan (např. 127): "))
            base_tilt = int(input("Zadejte výchozí hodnotu base_tilt (např. 127): "))
            light = Head(name, address, *params, base_pan=base_pan, base_tilt=base_tilt)
        elif light_type == "haze":
            haze = int(input("Zadejte hodnotu haze: "))
            fan = int(input("Zadejte hodnotu fan: "))
            light = Haze(name, address, haze, fan)
        else:
            print("Neplatný typ světla.")
            return

        self.lights.append(light)
        self.save_lights()
        print(f"Světlo '{light.name}' přidáno.")

    def remove_light(self):
        if not self.lights:
            print("Žádná světla k odstranění.")
            return

        print("Dostupná světla:")
        for i, light in enumerate(self.lights, start=1):
            print(f"{i}. {light.name} (Adresa: {light.address}, Typ: {type(light).__name__.lower()})")

        try:
            index = int(input("Zadejte číslo světla ke smazání: ")) - 1
            if 0 <= index < len(self.lights):
                removed_light = self.lights.pop(index)
                self.save_lights()
                print(f"Světlo '{removed_light.name}' bylo úspěšně odstraněno.")
            else:
                print("Neplatné číslo.")
        except ValueError:
            print("Neplatný vstup.")

    def list_lights(self):
        if not self.lights:
            print("Žádná světla nenalezena.")
            return
        for light in self.lights:
            print(light)

def main():
    plot = LightPlot("light_plot.txt")

    while True:
        print("\n1. Přidat světlo\n2. Smazat světlo\n3. Zobrazit světla\n4. Ukončit")
        choice = input("Vyberte možnost: ").strip()

        if choice == "1":
            plot.add_light()
        elif choice == "2":
            plot.remove_light()
        elif choice == "3":
            plot.list_lights()
            input("Stiskněte Enter pro pokračování...")
        elif choice == "4":
            break
        else:
            print("Neplatná volba.")

if __name__ == "__main__":
    main()
