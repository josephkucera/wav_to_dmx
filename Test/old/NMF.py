# Importování potřebných knihoven pro audio zpracování a vizualizaci
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import scipy.signal
from sklearn.decomposition import NMF
import json
from pathlib import Path
from collections import Counter
import re

# Třída pro vizualizaci výsledků NMF dekompozice
class NMFPlotter:
    def __init__(self, stft, activations, bases, sr, n_fft, highlighted_ranges):
        # Inicializace s parametry pro grafy
        self.stft = stft
        self.activations = activations
        self.bases = bases
        self.sr = sr
        self.n_fft = n_fft
        self.highlighted_ranges = highlighted_ranges

    def plot(self):
        # Výpočet frekvencí pro X osu grafu
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)
        plt.figure(figsize=(12, 10))

        # Graf spektrogramu
        plt.subplot(4, 1, 1)
        librosa.display.specshow(librosa.amplitude_to_db(np.abs(self.stft)), sr=self.sr, x_axis='time', y_axis='log')
        plt.title('Spectrogram')

        # Graf aktivací NMF komponent
        plt.subplot(4, 1, 2)
        for act in self.activations:
            plt.plot(act)
        plt.title('NMF Activations')

        # Graf základních komponent NMF
        plt.subplot(4, 1, 3)
        for i, basis in enumerate(self.bases):
            plt.plot(basis, label=f'Component {i}')
        plt.title('NMF Bases')
        plt.legend()

        # Graf FFT základních komponent
        plt.subplot(4, 1, 4)
        for i, basis in enumerate(self.bases):
            plt.stem(freqs, basis, linefmt=f'C{i}-', markerfmt=f'C{i}o', basefmt=" ", label=f'Component {i}')
            if i < len(self.highlighted_ranges):
                low, high = self.highlighted_ranges[i]
                plt.axvspan(low, high, color=f'C{i}', alpha=0.2)
        plt.xscale('log')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude')
        plt.title('FFT of Filtered NMF Bases')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend()
        plt.tight_layout()
        plt.show()

# Třída pro exportování NMF dekompozice do souborů
class NMFExporter:
    def __init__(self, audio_path, sr, n_components, n_fft, hop_length, activations, bases):
        # Inicializace s parametry pro export
        self.audio_path = audio_path
        self.sr = sr
        self.n_components = n_components
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.activations = activations
        self.bases = bases

    def save_to_json(self):
        # Uložení NMF dekompozice do JSON souboru
        audio_file_stem = Path(self.audio_path).stem
        json_path = f'{audio_file_stem}-decomposition.json'

        data = {
            'n_components': self.n_components,
            'n_fft': self.n_fft,
            'hop_length': self.hop_length,
            'sr': self.sr,
            'audio_path': self.audio_path,
            'acts': self.activations.tolist(),
            'bases': self.bases.tolist()
        }

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

        return json_path

    def write_to_file(self, y, output_path):
        # Uložení resynthesized audio do souboru
        sf.write(output_path, y, self.sr, subtype='PCM_24')

# Třída pro dekompozici audio signálu pomocí NMF
class DecomposeNMF:
    def __init__(self, audio_path, n_components=5, n_fft=1024, hop_length=None, duration_seconds=None):
        # Inicializace třídy a načítání audio souboru
        self.audio_path = audio_path
        self.n_components = n_components
        self.n_fft = n_fft
        self.hop_length = hop_length or n_fft // 2
        self.duration_seconds = duration_seconds
        self.highlighted_ranges = []
        self.fft_settings = {'n_fft': self.n_fft, 'hop_length': self.hop_length}
        self.audio_buffer, self.sr = librosa.load(audio_path, sr=None, mono=True, duration=duration_seconds)
        self.stft = librosa.stft(self.audio_buffer, **self.fft_settings)
        self.original_mags = np.abs(self.stft)
        self.original_phases = np.angle(self.stft)
        self.bases, self.activations = self.decompose(self.original_mags)
        self.exporter = NMFExporter(audio_path, self.sr, self.n_components, self.n_fft, self.hop_length, self.activations, self.bases)

    def hz_to_note_name(self, hz):
        # Převod frekvence na název noty
        return librosa.hz_to_note(hz)
    

    def get_most_common_keys(self):
        # Inicializujeme prázdný seznam pro klíče
        keys = []

        # Pro každou složku dekompozice (basis)
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)

        for i, basis in enumerate(self.bases):
            # Získáme 3 nejvyšší frekvence pro každou složku
            top_indices = np.argsort(basis)[-3:][::-1]
            top_freqs = freqs[top_indices]
            note_names = [self.hz_to_note_name(f) for f in top_freqs]

            # Odstraníme čísla na konci tónu pomocí regulárního výrazu
            note_names_cleaned = [re.sub(r'\d', '', note) for note in note_names]

            # Přidáme očištěné tóny do seznamu keys
            keys.extend(note_names_cleaned)

        # Spočítáme počet výskytů každého tónu
        note_counts = Counter(keys)

        # Filtrujeme tóny, které se objevují alespoň 2x
        filtered_note_counts = {note: count for note, count in note_counts.items() if count >= 2}

        # Seřadíme tóny podle četnosti výskytu (od nejčastějšího po nejméně častý)
        sorted_note_counts = sorted(filtered_note_counts.items(), key=lambda x: x[1], reverse=True)

        # Vytiskneme seznam tónů a jejich výskytů
        print("Tóny a jejich výskyt (seřazené od nejčastějšího po nejméně častý):")
        for note, count in sorted_note_counts:
            print(f"{note}: {count}")


    def decompose(self, mags):
        # Dekompozice pomocí NMF
        nmf_model = NMF(n_components=self.n_components, solver='mu', beta_loss='itakura-saito')
        acts = nmf_model.fit_transform(np.transpose(mags))
        bases = nmf_model.components_
        acts = np.transpose(acts)
        return bases, acts

    def compute_rms(self, y):
        # Výpočet RMS (root mean square) hodnoty pro audio signál
        return np.sqrt(np.mean(y**2))

    def normalize_audio(self, y, target_rms=0.1):
        # Normalizace audio signálu na požadovanou RMS hodnotu
        rms = self.compute_rms(y)
        if rms > 0:
            y = y * (target_rms / rms)
        return y

    def _make_mags_from_basis_and_activation(self, activation, basis):
        # Vytvoření magnitudy z aktivace a základní komponenty
        return np.outer(basis, activation)

    def _balance_mags_via_softmask(self, resynthesized_mags, mags_to_mask):
        # Vyvážení magnitudy pomocí softmasking techniky
        multiplier = 1 / np.maximum(np.sum(resynthesized_mags, axis=0), 1e-10)
        return multiplier * resynthesized_mags * mags_to_mask

    def _make_complex_matrix_from_mags_and_phases(self, mags, phases):
        # Vytvoření komplexní matice z magnitudy a fáze
        return mags * np.exp(1j * phases)

    def _istft(self, complex_stft):
        # Inverzní STFT transformace pro získání audio signálu
        return librosa.istft(complex_stft, **self.fft_settings)

    def assign_frequency_bins(self):
        # Přiřazení frekvenčních binů k NMF komponentám
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)
        octave_edges = [50, 110, 220, 440, 880, 1760, 3520, 7040]
        num_bands = len(octave_edges) - 1
        band_votes = []

        # Hledání nejvyšších frekvencí pro každou komponentu
        for i, basis in enumerate(self.bases):
            top_indices = np.argsort(basis)[-3:][::-1]
            top_freqs = freqs[top_indices]
            note_names = [self.hz_to_note_name(f) for f in top_freqs]
            print(f"Component {i} top frequencies:")
            for f, note in zip(top_freqs, note_names):
                print(f"  {f:.2f} Hz ({note})")
            for f in top_freqs:
                for j in range(num_bands):
                    if octave_edges[j] <= f < octave_edges[j+1]:
                        band_votes.append((i, j))

        vote_matrix = np.zeros((len(self.bases), num_bands))
        for comp_idx, band_idx in band_votes:
            vote_matrix[comp_idx, band_idx] += 1

        # Přiřazení komponent k frekvenčním pásmům
        assignments = []
        assigned_components = set()
        assigned_bands = set()

        while len(assignments) < min(len(self.bases), num_bands):
            max_votes = -1
            best_pair = (None, None)
            for i in range(len(self.bases)):
                if i in assigned_components:
                    continue
                for j in range(num_bands):
                    if j in assigned_bands:
                        continue
                    if vote_matrix[i, j] > max_votes:
                        max_votes = vote_matrix[i, j]
                        best_pair = (i, j)
            if best_pair[0] is not None:
                assignments.append(best_pair)
                assigned_components.add(best_pair[0])
                assigned_bands.add(best_pair[1])

        # Přiřazení zbývajících komponent k pásmům
        for i in range(len(self.bases)):
            if i not in assigned_components:
                for j in range(num_bands):
                    if j not in assigned_bands:
                        assignments.append((i, j))
                        assigned_components.add(i)
                        assigned_bands.add(j)
                        break

        masks_and_ranges = []
        for i, j in sorted(assignments):
            low_freq = octave_edges[j]
            high_freq = octave_edges[j + 1]
            bin_mask = (freqs >= low_freq) & (freqs < high_freq)
            masks_and_ranges.append((bin_mask, (low_freq, high_freq)))

        return masks_and_ranges

    def apply_filters(self):
        # Použití filtrů na základní komponenty
        masks_and_ranges = self.assign_frequency_bins()
        for i, (mask, (low_freq, high_freq)) in enumerate(masks_and_ranges):
            filtered_basis = np.zeros_like(self.bases[i])
            filtered_basis[mask] = self.bases[i][mask]
            self.bases[i] = filtered_basis
            self.highlighted_ranges.append((low_freq, high_freq))
            print(f"Component {i}: Assigned unique band {low_freq:.1f} Hz - {high_freq:.1f} Hz")

    def resynthesize(self, normalize=True):
        # Resyntéza signálů na základě komponent
        resynthesized_mags = [self._make_mags_from_basis_and_activation(self.activations[i], self.bases[i]) for i in range(self.n_components)]
        masked_mags = self._balance_mags_via_softmask(resynthesized_mags, self.original_mags)

        if normalize:
            rms_values = []
            for i in range(self.n_components):
                y = self._istft(self._make_complex_matrix_from_mags_and_phases(masked_mags[i], self.original_phases))
                rms_values.append(self.compute_rms(y))
            target_rms = np.mean(rms_values)

            for i in range(self.n_components):
                y = self._istft(self._make_complex_matrix_from_mags_and_phases(masked_mags[i], self.original_phases))
                y = self.normalize_audio(y, target_rms)
                self.exporter.write_to_file(y, f'component-{i}.wav')
        else:
            for i in range(self.n_components):
                y = self._istft(self._make_complex_matrix_from_mags_and_phases(masked_mags[i], self.original_phases))
                self.exporter.write_to_file(y, f'component-{i}.wav')

    def plot(self):
        # Vykreslení grafů dekompozice
        plotter = NMFPlotter(self.stft, self.activations, self.bases, self.sr, self.n_fft, self.highlighted_ranges)
        plotter.plot()

    def export_json(self):
        # Exportování dekompozice do JSON
        self.exporter.save_to_json()

# Hlavní funkce pro spuštění dekompozice a její vizualizace
def main():
    audio_path = "Test/sound/mixdown.wav"
    model = DecomposeNMF(audio_path, n_components=5, n_fft=4096)
    model.apply_filters()
    model.export_json()
    model.resynthesize(normalize=True)
    common_keys = model.get_most_common_keys()
    model.plot()
# Získání a vytištění nejčastějších tónů

    
# Spuštění programu, pokud je tento soubor hlavní
if __name__ == '__main__':
    main()
