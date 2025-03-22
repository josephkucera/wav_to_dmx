import numpy as np

# Funkce pro výpočet BPM z časů mezi špičkami
def calculate_bpm(peak_times, FRAMES_PER_BUFFER):
    """ Kalkulace BPM z načtených špiček """
    time_diff = []

    for i in range(2, 7, 2):
        diff = peak_times[i] + FRAMES_PER_BUFFER - peak_times[i-2] + (FRAMES_PER_BUFFER * (peak_times[i+1] - 1))
        time_diff.append(diff)

    time_diff_mean = np.median(time_diff)
    bpm = round(60 / (time_diff_mean / (FRAMES_PER_BUFFER) * 0.2))

    print(f"Aktuální BPM: {bpm}")
    return bpm

# Funkce pro detekci špiček a výpočet BPM (uchovává poslední BPM)
def bpm_timing(buffer_data, peak_times, peak_times_index, peak_buffer_index, FRAMES_PER_BUFFER):
    """ Funkce počítá BPM pouze při dosažení určitého počtu špiček,
        jinak vrací poslední známé BPM.
    """
    bpm_timing.last_bpm: int
    threshold = 400  # Prahová hodnota pro detekci špičky
    if not hasattr(bpm_timing, "last_bpm"):  
        bpm_timing.last_bpm = 0  # Inicializace pouze při prvním spuštění

    if peak_buffer_index > 20:  
        peak_times = [] 
        peak_times_index = 0 
        peak_buffer_index = 0 
        print("Vynulování")

        peak_boll = 0
        return bpm_timing.last_bpm, peak_boll, peak_times, peak_times_index, peak_buffer_index

    if np.max(buffer_data) <= threshold:
        peak_buffer_index += 1 if peak_buffer_index > 0 else 0
        peak_boll = 0
        return bpm_timing.last_bpm, peak_boll, peak_times, peak_times_index, peak_buffer_index

    elif np.max(buffer_data) > threshold and peak_times_index == 0:  
        peak_times.append(np.argmax(buffer_data)) 
        peak_times.append(0)
        peak_buffer_index = 1
        peak_times_index = 1
        print("\nZaregistrovaná špičková hodnota, začínám výpočet \nzbývá hodnot | 3")

        peak_boll = 1
        return bpm_timing.last_bpm, peak_boll, peak_times, peak_times_index, peak_buffer_index

    elif np.max(buffer_data) > threshold and peak_times_index == 1:  
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print("\nZbývá hodnot | 2")
        peak_times_index = 2
        peak_buffer_index = 1

        peak_boll = 1
        return bpm_timing.last_bpm, peak_boll, peak_times, peak_times_index, peak_buffer_index

    elif np.max(buffer_data) > threshold and peak_times_index == 2:  
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print("\nZbývá hodnot | 1")
        peak_times_index = 3
        peak_buffer_index = 1

        peak_boll = 1
        return bpm_timing.last_bpm, peak_boll, peak_times, peak_times_index, peak_buffer_index

    elif np.max(buffer_data) > threshold and peak_times_index == 3:
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print("\nZbývá hodnot | 0")

        # Vypočítáme nové BPM
        bpm_timing.last_bpm = calculate_bpm(peak_times, FRAMES_PER_BUFFER)
        peak_times = []
        peak_times_index = 0

        peak_boll = 1
        return bpm_timing.last_bpm, peak_boll, peak_times, peak_times_index, peak_buffer_index

