import numpy as np
import matplotlib.pyplot as plt
import filter as filter
import fft as fft



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
    signal_2 = 0.5*(np.sin(2 * np.pi * f2 * t))  # druhá sinusová vlna

    # Součet signálů
    signal = signal_1 + signal_2
    return signal


# def plot_all_graphs(signal, filtered_signal_lp, fft_freq, fft_result, fs):
def plot_all_graphs(signal, filtered_signal_lp, fft_freq, fft_result, fft_freq_filt, fft_result_filt, fs):

    """
    Funkce pro vykreslení všech grafů v jednom okně:
    1. Signál před a po filtraci
    2. Signál v časové doméně
    3. FFT (frekvenční spektrum)
    """
    plt.figure(figsize=(12, 10))

    # První podgraf - Původní signál
    plt.subplot(2, 2, 1)  # (počet řádků, počet sloupců, index subgrafu)
    plt.plot(signal, color='blue', label='Původní signál')
    plt.title('Původní signál')
    plt.xlabel('Vzorky')
    plt.ylabel('Amplituda')
    plt.grid(True)

    # Druhý podgraf - Signál po filtraci
    plt.subplot(2, 2, 2)
    plt.plot(filtered_signal_lp, color='red', label='Po filtraci')
    plt.title('Signál po filtraci')
    plt.xlabel('Vzorky')
    plt.ylabel('Amplituda')
    plt.grid(True)

    # Třetí podgraf - FFT (frekvenční spektrum)
    plt.subplot(2, 2, 3)
    plt.plot(fft_freq, fft_result, color='red')
    plt.title("FFT Původní signál (Frekvenční spektrum)")
    plt.xlabel("Frekvence [Hz]")
    plt.ylabel("Amplituda (normalizováno na 8-bit)")
    plt.grid(True)
    
    # Čtvrtý podgraf - FFT (frekvenční spektrum)
    plt.subplot(2, 2, 4)
    plt.plot(fft_freq_filt, fft_result_filt, color='red')
    plt.title("FFT filtrovavný signál (Frekvenční spektrum)")
    plt.xlabel("Frekvence [Hz]")
    plt.ylabel("Amplituda (normalizováno na 8-bit)")
    plt.grid(True)

    # Zobrazení všech grafů
    plt.tight_layout()
    plt.show()


# Příklad použití:
fs = 44100  # vzorkovací frekvence (Hz)
duration = 1  # délka signálu (v sekundách)
f1 = 500
f2 = 20

# Generování součtu dvou sinusových signálů: 1000 Hz a 100 Hz
signal = generate_signal(fs, duration, f1, f2)

# Tvorba filtru
filtered_signal_lp = filter.create_filter(signal, 'LP', fs, 200)

# Provádění FFT na signálu
fft_freq, fft_result = fft.perform_fft(signal, fs)
fft_freq_filt, fft_result_filt = fft.perform_fft(filtered_signal_lp, fs)

# Normalizace výsledků FFT na 8-bit
normalized_fft_result = fft.normalize_fft(fft_result)
normalized_fft_result_filt = fft.normalize_fft(fft_result_filt)


# Zobrazení všech grafů v jednom okně
# plot_all_graphs(signal, filtered_signal_lp, fft_freq, normalized_fft_result, fs)
plot_all_graphs(signal, filtered_signal_lp, fft_freq, normalized_fft_result, fft_freq_filt, normalized_fft_result_filt, fs)