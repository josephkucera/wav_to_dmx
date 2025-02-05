import numpy as np
import matplotlib.pyplot as plt
import filter as filter
import fft as fft


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
    signal_2 = 0.5*(np.sin(2 * np.pi * f2 * t))  # druhá sinusová vlna

    # Součet signálů
    signal = signal_1 + signal_2
    return signal

# Příklad použití:
fs = 44100  # vzorkovací frekvence (Hz)
duration = 1  # délka signálu (v sekundách)
f1 = 500
f2 = 20

# Generování součtu dvou sinusových signálů: 1000 Hz a 100 Hz
signal = generate_signal(fs, duration, f1, f2)

# Tvorba filtru
filtered_signal_lp = filter.create_filter(signal, 'LP', fs, 200)


# Zobrazení signálu před a po filtraci
plot_signal_before_after(signal, filtered_signal_lp)

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
    plt.plot(np.arange(len(signal)) / fs, signal, color='blue')  # Normalizuj podle vzorkovací frekvence
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


# Provádění FFT na signálu
fft_freq, fft_result = fft.perform_fft(signal, fs)

# Normalizace výsledků FFT na 8-bit
normalized_fft_result = fft.normalize_fft(fft_result)

# Nalezení 3 nejvíce zastoupených frekvencí (s normalizovanými amplitudami)
dominant_frequencies = fft.find_dominant_frequencies(fft_freq, normalized_fft_result)

# Výpis dominantních frekvencí s jejich amplitudami v normalizovaném rozsahu (0-255)
print("Dominantní frekvence a jejich normalizované amplitudy:")
for freq, amplitude in dominant_frequencies:
    print(f"Frekvence: {freq:.2f} Hz, Amplituda: {amplitude:.2f}")

# Zobrazení signálu a jeho FFT
plot_signal_and_fft(signal, fft_freq, normalized_fft_result, duration, fs)
