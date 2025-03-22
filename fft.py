import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq


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

