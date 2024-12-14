import time
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
 
start_time = time.perf_counter()

# Parametry pro záznam
RATE = 16000
FRAMES_PER_BUFFER = round(RATE / 5)  # 3200 vzorků na jeden buffer (0.2 sekundy)
FORMAT = pyaudio.paInt16
CHANNELS = 1


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
seconds = 20
data = np.array([], dtype=np.int16)  # Inicializace prázdného pole pro všechny vzorky
data_for_plot = np.array([], dtype=np.int16)

# Počet úseků na jednu sekundu
samples_per_second = RATE // FRAMES_PER_BUFFER

# Maximální hodnota pro 16-bitový zvuk
max_amplitude = 32767  # Pro 16-bitové audio (2 na 16) / 2 

# Hlavní smyčka pro čtení dat
for i in range(0, int((RATE / FRAMES_PER_BUFFER) * seconds)):
    buffer_data = stream.read(FRAMES_PER_BUFFER)
    # Převedení binárních dat na numpy array a přidání k celkovým datům pro danou sekundu
    data = np.concatenate((data, np.frombuffer(buffer_data, dtype=np.int16)))
    
    # Počet vzorků na jednu sekundu
    if len(data) >= RATE:  # Jakmile máme vzorky pro 1 sekundu (16000 vzorků)
        # Výpočet střední efektivní hodnoty (RMS) pro všechny vzorky za tuto sekundu
        rms = np.sqrt(np.mean(np.square(data[-RATE:])))
        
        # Převod RMS na decibely (dB)
        if rms > 0:  # Abychom předešli dělení nulou
            dB = 20 * np.log10(rms / max_amplitude)
        else:
            dB = -np.inf  # Pokud je RMS 0 (např. ticho), vrátíme -nekonečno (nebo můžeš zvolit nějakou jinou hodnotu)

         # Vytisknutí RMS a dB hodnoty pro každou sekundu, s formátováním na 2 desetinná místa
        print(f"RMS (sekunda {i // samples_per_second + 1}): {rms:.2f}  |  dB: {dB:.2f}")

        data_for_plot = np.concatenate((data_for_plot, data), axis=None) # uložení dat pro vyplotění
        # Resetování dat pro další sekundu
        data = np.array([], dtype=np.int16)

# Ukončení streamu
stream.stop_stream()
stream.close()
p.terminate()



print("\nStop recording")
end_time = time.perf_counter()

elapsed_time = end_time - start_time
print(f"Čas vykonání kódu: {elapsed_time: .3f} sekund")


#Jednoduché vyplotění signálu. 
plt.figure(figsize=(15,5))
plt.plot(data_for_plot)
plt.title("Audio signal")
plt.ylabel("Amplituda")
plt.xlabel("Vzorky [n]")
plt.show()