import numpy as np
from scipy.signal import butter, lfilter

def create_filter(signal, filter_type, fs, f1, f2=None, quality=12):
    """
    Vytvoří filtr podle typu filtru, kvality a frekvencí.

    Parameters:
    - signal: vstupní signál (numpy array)
    - filter_type: 'HP' pro High Pass, 'LP' pro Low Pass, 'BP' pro Band Pass
    - fs: vzorkovací frekvence (Hz)
    - f1: dolní mezní frekvence (Hz)
    - f2: horní mezní frekvence (pokud je použitý BP filtr)
    - quality: kvalita filtru (12, 24 nebo 32 dB na oktávu)

    Returns:
    - filtr: upravený signál
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
        raise ValueError("Neplatný typ filtru. Použijte 'HP', 'LP' nebo 'BP'.")

    # Kvalita filtru (Q)
    if quality == 12:
        Q = 0.707  # To odpovídá 12 dB na oktávu
    elif quality == 24:
        Q = 1 / np.sqrt(2)  # To odpovídá 24 dB na oktávu
    elif quality == 32:
        Q = 1 / 3  # To odpovídá 32 dB na oktávu
    else:
        raise ValueError("Neplatná kvalita filtru. Použijte 12, 24 nebo 32 dB na oktávu.")
    
    # Výpočet parametrů filtru
    nyquist = 0.5 * fs
    low = lowcut / nyquist if lowcut is not None else None
    high = highcut / nyquist if highcut is not None else None

    # Navrhování filtru (butterworth)
    b, a = butter(4, [low, high], btype=filter_type.lower(), output='ba', analog=False)

    # Aplikace filtru
    filtered_signal = lfilter(b, a, signal)

    return filtered_signal

# Příklad použití:
fs = 1000  # vzorkovací frekvence (Hz)
signal = np.random.randn(1000)  # generování náhodného signálu jako ukázka

# Použití High Pass filtru s 12 dB/oktávu a frekvencí 100 Hz
filtered_signal_hp = create_filter(signal, 'HP', fs, 100, quality=12)

# Použití Low Pass filtru s 12 dB/oktávu a frekvencí 300 Hz
filtered_signal_lp = create_filter(signal, 'LP', fs, 300, quality=12)

# Použití Band Pass filtru mezi 100 Hz a 300 Hz s kvalitou 24 dB na oktávu
filtered_signal_bp = create_filter(signal, 'BP', fs, 100, 300, quality=24)
