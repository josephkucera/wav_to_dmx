import numpy as np
import matplotlib.pyplot as plt
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

    # Ověření, že kritické frekvence jsou v rozsahu (0, 1) po normalizaci
    if low is not None and (low <= 0 or low >= 1):
        raise ValueError(f"Pro filtr {filter_type} musí být 'lowcut' mezi 0 a {nyquist} Hz.")
    if high is not None and (high <= 0 or high >= 1):
        if high == 1:  # U Low Pass filtru nemůže být `highcut` rovno Nyquistově frekvenci
            raise ValueError(f"Pro filtr {filter_type} musí být 'highcut' menší než Nyquistova frekvence ({nyquist} Hz).")
        raise ValueError(f"Pro filtr {filter_type} musí být 'highcut' mezi 0 a {nyquist} Hz.")

    # Pokud je lowcut None a používáme LP filtr nebo highcut None a používáme HP filtr,
    # tak to znamená, že máme neúplné parametry.
    if (filter_type == 'HP' and lowcut is None) or (filter_type == 'LP' and highcut is None):
        raise ValueError(f"Pro filtr typu {filter_type} musí být specifikována frekvence.")

    # Navrhování filtru (butterworth)
    if filter_type == 'HP':
        b, a = butter(4, low, btype='highpass', output='ba', analog=False)
    elif filter_type == 'LP':
        b, a = butter(4, high, btype='lowpass', output='ba', analog=False)
    elif filter_type == 'BP':
        b, a = butter(4, [low, high], btype='bandpass', output='ba', analog=False)

    # Aplikace filtru
    filtered_signal = lfilter(b, a, signal)

    return filtered_signal

def plot_signal_before_after(signal, filtered_signal):
    """
    Funkce pro vykreslení signálu před a po filtraci.

    Parameters:
    - signal: původní signál (numpy array)
    - filtered_signal: upravený signál po aplikaci filtru (numpy array)
    """
    # Vytvoření grafu
    plt.figure(figsize=(10, 6))

    # Původní signál
    plt.subplot(2, 1, 1)
    plt.plot(signal, color='blue', label='Původní signál')
    plt.title('Původní signál')
    plt.xlabel('Vzorky')
    plt.ylabel('Amplituda')
    plt.grid(True)

    # Upravený signál
    plt.subplot(2, 1, 2)
    plt.plot(filtered_signal, color='red', label='Po filtraci')
    plt.title('Signál po filtraci')
    plt.xlabel('Vzorky')
    plt.ylabel('Amplituda')
    plt.grid(True)

    # Zobrazení grafu
    plt.tight_layout()
    plt.show()

def generate_signal(fs, duration, f1, f2):
    """
    Funkce pro generování signálu jako součet dvou sinusových vln (f1 a f2).

    Parameters:
    - fs: vzorkovací frekvence (Hz)
    - duration: délka signálu v sekundách
    - f1: frekvence první složky (Hz)
    - f2: frekvence druhé složky (Hz)

    Returns:
    - signal: generovaný signál (numpy array)
    """
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)  # časová osa
    signal_1 = np.sin(2 * np.pi * f1 * t)  # první sinusová vlna
    signal_2 = np.sin(2 * np.pi * f2 * t)  # druhá sinusová vlna

    # Součet signálů
    signal = signal_1 + signal_2
    return signal

# Příklad použití:
fs = 1000  # vzorkovací frekvence (Hz)
duration = 1  # délka signálu (v sekundách)

# Generování součtu dvou sinusových signálů: 1000 Hz a 100 Hz
signal = generate_signal(fs, duration, 100, 200)

# Použití Low Pass filtru s 12 dB/oktávu a frekvencí 500 Hz
filtered_signal_lp = create_filter(signal, 'LP', fs, 150, quality=12)

# Zobrazení signálu před a po filtraci
plot_signal_before_after(signal, filtered_signal_lp)
