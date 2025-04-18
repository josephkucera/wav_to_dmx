import Nopipeline.AudioClass as aud
import Nopipeline.DmxControll as dmx
import Nopipeline.VectorClass as VClass

# vytvoření objektů pro audio analýzu, světla a převodní vektor
audio  = aud.AudioAnalysis()
light  = dmx.LightManager()
vector = VClass.VectorClass(audio,light)



print("Začátek nahrávání, ukončení pomocí ctrl+c")

# hlavní loop programu
while True:
    try:
        audio.AudioProcessing()  # Zpracování zvuku
        vector.UpdateLights()  # Aktualizace hodnoty beat

    except KeyboardInterrupt:
        light.cleanup()
        audio.cleanup()

