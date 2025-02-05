import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

def generate_signal(fs, duration, f1, f2, f3):
    """
    Funkce pro generování signálu jako součet dvou sinusových vln (f1, f2 a f3).

    Parameters:
    - fs: vzorkovací frekvence (Hz)
    - duration: délka signálu v sekundách
    - f1: frekvence první složky (Hz)
    - f2: frekvence druhé složky (Hz)
    - f3: frekvence třetí složky (Hz)

    Returns:
    - signal: generovaný signál (numpy array)
    """
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)  # časová osa
    signal_1 = 2 * (np.sin(2 * np.pi * f1 * t))  # první sinusová vlna
    signal_2 = np.sin(2 * np.pi * f2 * t)  # druhá sinusová vlna
    signal_3 = 0.5 * (np.sin(2 * np.pi * f3 * t))  # třetí sinusová vlna

    # Součet signálů
    signal = signal_1 + signal_2 + signal_3
    return signal, t

def perform_fft(signal, fs):
    """
    Funkce pro provedení FFT (Fast Fourier Transform) na signálu.

    Parameters:
    - signal: vstupní signál (numpy array)
    - fs: vzorkovací frekvence (Hz)

    Returns:
    - freq: frekvence (numpy array)
    - fft_result: FFT výsledek (numpy array)
    """
    N = len(signal)
    # Vypočítat FFT
    fft_result = fft(signal)
    # Vypočítat frekvence
    freq = fftfreq(N, d=1/fs)
    
    # Vrátíme pouze pozitivní frekvence (první polovinu spektra)
    positive_freq = freq[:N//2]
    positive_fft_result = np.abs(fft_result)[:N//2]

    return positive_freq, positive_fft_result

def normalize_fft(fft_result):
    """
    Funkce pro normalizaci FFT výsledků do rozsahu 0-255 (8-bit).

    Parameters:
    - fft_result: vstupní FFT výsledek (numpy array)

    Returns:
    - normalized_fft_result: normalizovaný FFT výsledek (numpy array)
    """
    max_val = np.max(fft_result)
    # Normalizujeme do rozsahu 0-255
    normalized_fft_result = (fft_result / max_val) * 255
    normalized_fft_result = np.clip(normalized_fft_result, 0, 255)  # zajistíme, že všechny hodnoty budou mezi 0 a 255

    return normalized_fft_result

def find_dominant_frequencies(fft_freq, fft_result, num_peaks=3):
    """
    Funkce pro nalezení nejvíce zastoupených frekvencí a jejich amplitud.

    Parameters:
    - fft_freq: pole frekvencí (numpy array)
    - fft_result: FFT výsledek (numpy array)
    - num_peaks: počet dominantních frekvencí, které chceme vrátit (default 3)

    Returns:
    - dominant_frequencies: pole obsahující dominantní frekvence a jejich amplitudy
    """
    # Najdeme indexy třech největších hodnot
    peak_indices = np.argsort(fft_result)[-num_peaks:][::-1]
    
    # Získáme odpovídající frekvence a amplitudy
    dominant_frequencies = [(fft_freq[i], fft_result[i]) for i in peak_indices]
    
    return dominant_frequencies

def plot_signal_and_fft(signal, fft_freq, fft_result, time, fs):
    """
    Funkce pro vykreslení signálu a jeho FFT (Frekvenční spektrum).

    Parameters:
    - signal: původní signál (numpy array)
    - fft_freq: frekvence pro FFT (numpy array)
    - fft_result: výsledek FFT (numpy array)
    - time: časová osa (numpy array)
    - fs: vzorkovací frekvence (Hz)
    """
    plt.figure(figsize=(12, 6))

    # Původní signál
    plt.subplot(2, 1, 1)
    plt.plot(time, signal, color='blue')
    plt.title("Původní signál v časové doméně")
    plt.xlabel("Čas [s]")
    plt.ylabel("Amplituda")
    plt.grid(True)

    # Normalizovaný FFT výsledek
    plt.subplot(2, 1, 2)
    plt.plot(fft_freq, fft_result, color='red')
    plt.title("Výsledek FFT (Frekvenční spektrum)")
    plt.xlabel("Frekvence [Hz]")
    plt.ylabel("Amplituda (normalizováno na 8-bit)")
    plt.grid(True)

    plt.tight_layout()
    plt.show()

# Příklad použití:
fs = 16000  # vzorkovací frekvence (Hz)
duration = 1  # délka signálu (v sekundách)

# Generování testovacího signálu: součet 100 Hz, 200 Hz a 500 Hz
signal, t = generate_signal(fs, duration, 100, 200, 500)

# Provádění FFT na signálu
fft_freq, fft_result = perform_fft(signal, fs)

# Normalizace výsledků FFT na 8-bit
normalized_fft_result = normalize_fft(fft_result)

# Nalezení 3 nejvíce zastoupených frekvencí (s normalizovanými amplitudami)
dominant_frequencies = find_dominant_frequencies(fft_freq, normalized_fft_result)

# Výpis dominantních frekvencí s jejich amplitudami v normalizovaném rozsahu (0-255)
print("Dominantní frekvence a jejich normalizované amplitudy:")
for freq, amplitude in dominant_frequencies:
    print(f"Frekvence: {freq:.2f} Hz, Amplituda: {amplitude:.2f}")

# Zobrazení signálu a jeho FFT
plot_signal_and_fft(signal, fft_freq, normalized_fft_result, t, fs)
