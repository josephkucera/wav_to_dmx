import time
import pyaudio
import numpy as np

# Parametry pro záznam
FRAMES_PER_BUFFER = 3200  # 3200 vzorků na jeden buffer (0.2 sekundy)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Iniciace PyAudio
p = pyaudio.PyAudio()

# Otevření audio streamu
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER    
)

print("Start recording")

# Délka záznamu (v sekundách)
seconds = 5
frames = []

# Počet úseků na jednu sekundu
samples_per_second = RATE // FRAMES_PER_BUFFER

# Hlavní smyčka pro čtení dat
for i in range(0, int((RATE / FRAMES_PER_BUFFER) * seconds)):
    data = stream.read(FRAMES_PER_BUFFER)
    frames.append(data) #funkce extend přikládá na konec // append "vnořuje" listy

    # Převedení binárních dat na numpy array
    audio_data = np.frombuffer(data, dtype=np.int16)

    # Výpočet střední efektivní hodnoty (RMS) pro každý buffer
    rms = np.sqrt(np.mean(np.square(audio_data)))

    # Vytisknutí RMS hodnoty každou vteřinu (agregace více úseků dat)
    if i % samples_per_second == 0:
        print(f"RMS (sekunda {i // samples_per_second}): {rms}")

# Ukončení streamu
stream.stop_stream()
stream.close()
p.terminate()


print("\nStop recording")

while True: 
    time.sleep(1)
    print ("furt jedu")


# načtu buffer a uložím ho do hodnoty data kam se uloží jako stojové číslo x01 x00 xff apod. 
# z toho potřebuju načíst víc hodnot 
# ctrl + . (import neimportované knihovny) 
# crtl + c (přerušení smyčky)

# Do příště
# Předělat na "nekonečnou smyčku", Vyprintit RMS za každou "proběhlou" vteřinu (ne buffer ale celá s) ať se vkládá za sebe
# Nějaký beat detection implementovat (metronom) >> Tempo

# Frekvenční filrty
# Fourierka? FFT 