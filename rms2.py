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
seconds = 10
data = np.array([], dtype=np.int16)  # Inicializace prázdného pole pro všechny vzorky

# Počet úseků na jednu sekundu
samples_per_second = RATE // FRAMES_PER_BUFFER

# Maximální hodnota pro 16-bitový zvuk
max_amplitude = 32767  # Pro 16-bitové audio

# Prahová hodnota pro detekci špičky
threshold_dB = -75  # dB

# Minimální časový rozdíl mezi špičkami v sekundách (125 ms)
min_time_diff = 0.125  # 125 ms

# Seznam pro uchování časů mezi špičkami
peak_times = []

# Funkce pro výpočet BPM z časů mezi špičkami
def calculate_bpm(peak_times):
    if len(peak_times) < 2:
        return None  # Pokud nemáme dostatek údajů
    time_differences = np.diff(peak_times)  # Rozdíly mezi časy špiček
    avg_time_diff = np.mean(time_differences)  # Průměrný časový rozdíl
    bpm = 60000 / avg_time_diff  # Převedení na BPM
    return bpm

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
        
        # Kontrola, zda překročí prahovou hodnotu pro detekci špičky
        if dB > threshold_dB:
            # Získáme aktuální čas
            peak_time = time.time()

            # Zkontrolujeme, zda rozdíl mezi poslední špičkou a aktuální špičkou není menší než 125 ms
            if len(peak_times) == 0 or (peak_time - peak_times[-1]) >= min_time_diff:
                # Uložíme čas špičky
                peak_times.append(peak_time)
                print(f"Peak detected at {peak_time} seconds (dB: {dB:.2f})")

                # Pokud máme dost
