
import numpy as np
import matplotlib.pyplot as plt


# Funkce pro výpočet BPM z časů mezi špičkami
def calculate_bpm(peak_times,FRAMES_PER_BUFFER):
    """ Kalkulace z prichoziho signalu """
    time_diff = []
    
    for i in range(2,7,2):
        diff = peak_times[i]+FRAMES_PER_BUFFER-peak_times[i-2]+(FRAMES_PER_BUFFER*(peak_times[i+1]-1))
        time_diff.append(diff)
    
    time_diff_mean = np.median(time_diff)

    bpm = (time_diff_mean / (FRAMES_PER_BUFFER) * 0.2 )  # přepočet na s
    bpm = round(60 / bpm)
    print(f"aktualni bpm je {bpm}")

def bpm_timing(buffer_data, peak_times, peak_times_index, peak_buffer_index, FRAMES_PER_BUFFER):
    """ Kalkulace z prichoziho signalu 
    - signal urceny k vypoctu
    - glob.prom obsahujici ulozene casy spicek
    - pocitadlo zaznamenanych peaku
    - pocitadlo pruchodu bez peaku 
    - delka bufferu """
    threshold = 400  # dB Prahová hodnota pro detekci špičky
    
    # Konverze buffer_data na numpy array typu int16
    buffer_data = np.frombuffer(buffer_data, dtype=np.int16)
    
    if peak_buffer_index > 20:  # pokud je mezi lokálními maximy víc jak 2 s vynuluje se všechno a jedem odznova
        peak_times = [] 
        peak_times_index = 0 
        peak_buffer_index = 0 
        print("vynulování")
        return peak_times, peak_times_index, peak_buffer_index
            
    if np.max(buffer_data) <= threshold: # pocitadlo pruchodu bez peaku
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
        print("\n Zaregistrovaná špičková hodnota, začínám výpočet \nzbýva hodnot | 3")

        return peak_times, peak_times_index, peak_buffer_index
    
    elif np.max(buffer_data) > threshold and peak_times_index == 1:  # načtu první hodnotu, přesáhne threshold
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print("\nzbýva hodnot | 2")
        peak_times_index = 2
        peak_buffer_index = 1

        return peak_times, peak_times_index, peak_buffer_index
    
    elif np.max(buffer_data) > threshold and peak_times_index == 2:  # načtu první hodnotu, přesáhne threshold
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print("\nzbýva hodnot | 1")
        peak_times_index = 3
        peak_buffer_index = 1

        return peak_times, peak_times_index, peak_buffer_index
    
    elif np.max(buffer_data) > threshold and peak_times_index == 3:
        peak_times.append(np.argmax(buffer_data))
        peak_times.append(peak_buffer_index)
        print("\nzbýva hodnot | 0")
        calculate_bpm(peak_times,FRAMES_PER_BUFFER)
        peak_times = []  # vyčištění proměnné pro další výpočet bpm
        peak_times_index = 0  # vynulování indexu
        return peak_times, peak_times_index, peak_buffer_index
