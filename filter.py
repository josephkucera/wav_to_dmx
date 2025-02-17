import numpy as np
from scipy.signal import butter, lfilter

def create_filter(signal, filter_type ='HP', fs= 44100, f1=200, f2=None,Q = 4):
    """
    Vytvoří filtr podle typu, kvality, a mezních frekvencí

    Parametry
    - signal: vstupní signál (numpy array)
    - filter_type: 'HP' pro Horní Propust, 'LP' pro Dolní Propust, 'BP' pro Pásmovou Propust
    - fs: vzorkovací frekvence (Hz)
    - f1: mezní frekvence (Hz) (dolní pokud je BP filtr)
    - f2: horní mezní frekvence (pokud je použitý BP filtr)
    - Q: Kvalita filtru resp. Ntý řád filtru (standardně 4)
        - Pokles = Q*6 dB / Oktávu (standardně 24 dB/okt)

    Vrací:
    - filtrovaný signál 
    """

    # Nastavení typu filtru
    if filter_type == 'HP':  # High Pass
        lowcut = f1
        highcut = None
    elif filter_type == 'LP':  # Low Pass
        lowcut = None
        highcut = f1
    elif filter_type == 'BP':  # Band Pass
        lowcut = f1
        highcut = f2
    else:
        raise ValueError("Neplatný typ! Použijte 'HP', 'LP' nebo 'BP'.")

    # Výpočet parametrů filtru
    nyquist = 0.5 * fs # nyquistův teorém 
    low = lowcut / nyquist if lowcut is not None else None # normalizace mezní frekvence
    high = highcut / nyquist if highcut is not None else None # normalizace mezní frekvence

    # Ověření, že kritické frekvence jsou v rozsahu (0, 1) po normalizaci
    if low is not None and (low <= 0 or low >= 1):
        raise ValueError(f"Pro filtr {filter_type} musí být 'lowcut' mezi 0 a {nyquist} Hz.")
    if high is not None and (high <= 0 or high >= 1):
        if high == 1:  # U Low Pass filtru nemůže být `highcut` rovno Nyquistově frekvenci
            raise ValueError(f"Pro filtr {filter_type} musí být 'highcut' menší než Nyquistova frekvence ({nyquist} Hz).")
        raise ValueError(f"Pro filtr {filter_type} musí být 'highcut' mezi 0 a {nyquist} Hz.")

    # Pokud je lowcut None a používáme LP filtr nebo highcut None a používáme HP filtr, tak to znamená, že máme chybu v parametrech.
    
    if (filter_type == 'HP' and lowcut is None) or (filter_type == 'LP' and highcut is None):
        raise ValueError(f"Pro filtr typu {filter_type} musí být specifikována frekvence.")

    # Návrh filtru (butterworth)
    if filter_type == 'HP':
        b, a = butter(Q, low, btype='highpass', output='ba', analog=False)
    elif filter_type == 'LP':
        b, a = butter(Q, high, btype='lowpass', output='ba', analog=False)
    elif filter_type == 'BP':
        b, a = butter(Q, [low, high], btype='bandpass', output='ba', analog=False)

    # Aplikace filtru
    filtered_signal = lfilter(b, a, signal)

    return filtered_signal