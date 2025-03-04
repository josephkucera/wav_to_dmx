import AudioClass as aud
import DMX as dmx
import AudioOutput as AudVector

# vytvoření objektů pro audio analýzu, světla a převodní vektor
audio  = aud.AudioAnalysis()
vector = AudVector.VectorClass(audio)
# light  = dmx.dmx_controller()


print("Začátek nahrávání, ukončení pomocí ctrl+c")

# hlavní loop programu
while True:
    try:
        audio.AudioProcessing()  # Zpracování zvuku
        vector.GetInfo()  # Aktualizace hodnoty beat

    except KeyboardInterrupt:
        audio.cleanup()

