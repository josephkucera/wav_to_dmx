import numpy as np
from scipy.signal import butter, filtfilt

def create_filter(signal, filter_type='HP', fs=44100, f1=200, f2=None, Q=4):
    """
    Vytvoří filtr podle typu, kvality a mezních frekvencí

    Parametry:
    - signal: vstupní signál (numpy array)
    - filter_type: 'HP' (High Pass), 'LP' (Low Pass), 'BP' (Band Pass)
    - fs: vzorkovací frekvence (Hz)
    - f1: dolní mezní frekvence (nebo hlavní u HP/LP)
    - f2: horní mezní frekvence (pouze pro BP)
    - Q: řád filtru (standardně 4, pokles = Q*6 dB/okt)

    Vrací:
    - filtrovaný signál
    """

    # Nastavení mezních frekvencí
    if filter_type == 'HP':
        lowcut = f1
        highcut = None
    elif filter_type == 'LP':
        lowcut = None
        highcut = f1
    elif filter_type == 'BP':
        lowcut = f1
        highcut = f2
    else:
        raise ValueError("Neplatný typ! Použijte 'HP', 'LP' nebo 'BP'.")

    # Normalizace podle Nyquistovy frekvence
    nyquist = 0.5 * fs
    low = lowcut / nyquist if lowcut is not None else None
    high = highcut / nyquist if highcut is not None else None

    if low is not None and (low <= 0 or low >= 1):
        raise ValueError(f"Pro filtr {filter_type} musí být 'lowcut' mezi 0 a {nyquist} Hz.")
    if high is not None and (high <= 0 or high >= 1):
        raise ValueError(f"Pro filtr {filter_type} musí být 'highcut' mezi 0 a {nyquist} Hz.")

    if (filter_type == 'HP' and lowcut is None) or (filter_type == 'LP' and highcut is None):
        raise ValueError(f"Pro filtr typu {filter_type} musí být specifikována frekvence.")

    # Návrh filtru
    if filter_type == 'HP':
        b, a = butter(Q, low, btype='highpass', analog=False)
    elif filter_type == 'LP':
        b, a = butter(Q, high, btype='lowpass', analog=False)
    elif filter_type == 'BP':
        b, a = butter(Q, [low, high], btype='bandpass', analog=False)

    # Aplikace filtru s ochranou
    try:
        filtered_signal = filtfilt(b, a, signal)
    except ValueError as e:
        print(f"[Filter Warning] Chyba při filtraci: {e}")
        return np.zeros_like(signal)

    return filtered_signal
