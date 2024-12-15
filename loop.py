import sys 
import pyaudio 
import numpy as np
import matplotlib.pyplot as plt


# Parametry pro záznam
RATE = 16000 # vzorkovací frekvence
FRAMES_PER_BUFFER = round(RATE / 5)  # 3200 vzorků na jeden buffer (0.2 sekundy)
FORMAT = pyaudio.paInt16 # formát resp. 16bit datová hloubka
CHANNELS = 1

# Parametry pro výpočet
signal = np.array([], dtype=np.int16)  # Inicializace prázdného pole pro všechny vzorky
samples_per_second = RATE // FRAMES_PER_BUFFER # Počet úseků na jednu sekundu
max_amplitude = 32767  # maximální amplituda Pro 16-bitové audio (2 na 16) / 2 
seconds = 0 # iniciace proměnné pro počítání odběhlého času



# Iniciace PyAudio
# Otevření audio streamu
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER    
)

print("Začátek nahrávání, ukončení pomocí ctrl+c")

# Hlavní smyčka pro čtení dat
while True:
    try:
        buffer_data = stream.read(FRAMES_PER_BUFFER)
        # Převedení binárních dat na numpy array a přidání k celkovým datům pro danou sekundu
        signal = np.concatenate((signal, np.frombuffer(buffer_data, dtype=np.int16)))
        
        # Počet vzorků na jednu sekundu
        if len(signal) >= RATE:  # Jakmile máme vzorky pro 1 sekundu (16000 vzorků)
            rms = np.sqrt(np.mean(np.square(signal[-RATE:]))) # Výpočet střední efektivní hodnoty (RMS) pro všechny vzorky za tuto sekundu

            
            # Převod RMS na decibely (dB)
            if rms > 0:  # Abychom předešli dělení nulou
                dB = 20 * np.log10(rms / max_amplitude)
            else:
                dB = -np.inf  # Pokud je RMS 0 (např. ticho), vrátíme -nekonečno (nebo můžeš zvolit nějakou jinou hodnotu)

            # Vytisknutí RMS a dB hodnoty pro každou sekundu, s formátováním na 2 desetinná místa
            seconds = seconds + 1 # jenom simple ukazatel kolik vteřin už odběhlo
            print(f"RMS (sekunda {seconds}): {rms:.2f}  |  dB: {dB:.2f}")

            # Resetování dat pro další sekundu
            signal = np.array([], dtype=np.int16)
    except KeyboardInterrupt:
        # Pokud dojde k přerušení (Ctrl+C), vykoná se tento kód
        print("\nProgram byl přerušen.")
        
        # Ukončení streamu
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("Vykonávám závěrečné kroky...")
        sys.exit(0)  # Ukončí program

# načtu buffer a uložím ho do hodnoty data kam se uloží jako stojové číslo x01 x00 xff apod. 
# z toho potřebuju načíst víc hodnot 
# ctrl + . (import neimportované knihovny) 
# crtl + c (přerušení smyčky)

# Do příště
# Předělat na "nekonečnou smyčku", Vyprintit RMS za každou "proběhlou" vteřinu (ne buffer ale celá s) ať se vkládá za sebe
# Nějaký beat detection implementovat (metronom) >> Tempo

# Frekvenční filrty
# Fourierka? FFT 