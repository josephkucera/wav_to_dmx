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

# Proměnné pro výpočty
seconds = 15
data = np.array([], dtype=np.int16)  # Inicializace prázdného pole pro všechny vzorky
data_for_plot = np.array([], dtype=np.int16)
samples_per_second = RATE // FRAMES_PER_BUFFER  # Počet úseků na jednu sekundu
max_amplitude = 32767  # Pro 16-bitové audio (2 na 16) / 2 

# Parametry pro výpočet BPM
peak_times = []  # Seznam pro uchování časů mezi špičkami
peak_times_index = 0  # index pro uchování bpm hodnoty
peak_buffer_index = 0  # index počitadla bufferů

# Funkce pro výpočet BPM z časů mezi špičkami
def calculate_bpm(peak_times):
    time_diff = []
    
    for i in range(2,7,2):
        diff = peak_times[i]+FRAMES_PER_BUFFER-peak_times[i-2]+(FRAMES_PER_BUFFER*(peak_times[i+1]-1))
        time_diff.append(diff)
    
    time_diff_mean = np.median(time_diff)
    
    print (f"\n  rozdíly časů \n {time_diff}\n prum hodnota {time_diff_mean}")
    bpm = (time_diff_mean / (FRAMES_PER_BUFFER) * 0.2 )  # přepočet na s
    bpm = round(60 / bpm)
    print(f"aktualni bpm je {bpm}")

def bpm_timing(buffer_data, peak_times, peak_times_index, peak_buffer_index):
    threshold = 400  # dB Prahová hodnota pro detekci špičky
    
    # Konverze buffer_data na numpy array typu int16
    buffer_data = np.frombuffer(buffer_data, dtype=np.int16)
    
    if peak_buffer_index > 20:  # pokud je mezi lokálními maximy víc jak 2 s vynuluje se všechno a jedem odznova
        peak_times = [] 
        peak_times_index = 0 
        peak_buffer_index = 0 
        print("vynulování")
        return peak_times, peak_times_index, peak_buffer_index
            
    if np.max(buffer_data) <= threshold:
        if peak_buffer_index == 0:
            return peak_times, peak_times_index, peak_buffer_index
        else:
            peak_buffer_index = peak_buffer_index + 1
            return peak_times, peak_times_index, peak_buffer_index
    
    elif np.max(buffer_data) > threshold and peak_times_index == 0:  # načtu první špičkovou hodnotu
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(0)
        peak_buffer_index = 1
        peak_times_index = 1
        print (f"\n hodnota casu 1 {peak_times} a ještě buffer {peak_buffer_index} ")
        return peak_times, peak_times_index, peak_buffer_index
    
    elif np.max(buffer_data) > threshold and peak_times_index == 1:  # načtu první hodnotu, přesáhne threshold
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print (f"\n hodnota casu 2 {peak_times} a ještě buffer {peak_buffer_index} ")
        peak_times_index = 2
        peak_buffer_index = 1

        return peak_times, peak_times_index, peak_buffer_index
    
    elif np.max(buffer_data) > threshold and peak_times_index == 2:  # načtu první hodnotu, přesáhne threshold
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print (f"\n hodnota casu 3 {peak_times} a ještě buffer {peak_buffer_index} ")
        peak_times_index = 3
        peak_buffer_index = 1

        return peak_times, peak_times_index, peak_buffer_index
    
    elif np.max(buffer_data) > threshold and peak_times_index == 3:
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print (f"\n hodnota casu 4 {peak_times} a ještě buffer {peak_buffer_index} ")
        calculate_bpm(peak_times)
        peak_times = []  # vyčištění proměnné pro další výpočet bpm
        peak_times_index = 0  # vynulování indexu
        return peak_times, peak_times_index, peak_buffer_index

# Hlavní smyčka pro čtení dat
for i in range(0, int((RATE / FRAMES_PER_BUFFER) * seconds)):
    buffer_data = stream.read(FRAMES_PER_BUFFER)
    # Převedení binárních dat na numpy array a přidání k celkovým datům pro danou sekundu
    data = np.concatenate((data, np.frombuffer(buffer_data, dtype=np.int16)))
    
    peak_times, peak_times_index, peak_buffer_index = bpm_timing(buffer_data, peak_times, peak_times_index, peak_buffer_index)

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
        # print(f"RMS (sekunda {i // samples_per_second + 1}): {rms:.2f}  |  dB: {dB:.2f}")

        data_for_plot = np.concatenate((data_for_plot, data), axis=None)  # uložení dat pro vyplotění
        # Resetování dat pro další sekundu
        data = np.array([], dtype=np.int16)

# Ukončení streamu
stream.stop_stream()
stream.close()
p.terminate()

print("\nStop recording")
end_time = time.perf_counter()

elapsed_time = end_time - start_time
print(f"Čas vykonání kódu: {elapsed_time:.3f} sekund")

# Jednoduché vyplotění signálu.
plt.figure(figsize=(15, 5))
plt.plot(data_for_plot)
plt.title("Audio signal")
plt.ylabel("Amplituda")
plt.xlabel("Vzorky [n]")
plt.show()
