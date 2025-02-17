import AudioClass as aud
# import lights as lights
import AudioOutput as AudVector

# vytvoření objektů pro audio analýzu, světla a převodní vektor
audio = aud.AudioAnalysis()
vector = AudVector.VectorClass(audio)
# light = lights.LightsControll()


print("Začátek nahrávání, ukončení pomocí ctrl+c")

# hlavní loop programu
while True:
    try:
        audio.AudioProcessing()  # Zpracování zvuku
        vector.GetInfo()  # Aktualizace hodnoty beat

    except KeyboardInterrupt:
        audio.cleanup()

