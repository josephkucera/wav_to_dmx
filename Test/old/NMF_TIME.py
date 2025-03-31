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

class NMFPlotter:
    def __init__(self, stft, activations, bases, sr, n_fft, highlighted_ranges):
        self.stft = stft
        self.activations = activations
        self.bases = bases
        self.sr = sr
        self.n_fft = n_fft
        self.highlighted_ranges = highlighted_ranges

    def plot(self):
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)
        plt.figure(figsize=(12, 10))
        plt.subplot(4, 1, 1)
        librosa.display.specshow(librosa.amplitude_to_db(np.abs(self.stft)), sr=self.sr, x_axis='time', y_axis='log')
        plt.title('Spectrogram')

        plt.subplot(4, 1, 2)
        for act in self.activations:
            plt.plot(act)
        plt.title('NMF Activations')

        plt.subplot(4, 1, 3)
        for i, basis in enumerate(self.bases):
            plt.plot(basis, label=f'Component {i}')
        plt.title('NMF Bases')
        plt.legend()

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

class NMFExporter:
    def __init__(self, audio_path, sr, n_components, n_fft, hop_length, activations, bases):
        self.audio_path = audio_path
        self.sr = sr
        self.n_components = n_components
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.activations = activations
        self.bases = bases

    def save_to_json(self):
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
        sf.write(output_path, y, self.sr, subtype='PCM_24')

class DecomposeNMF:
    def __init__(self, audio_path, n_components=5, n_fft=1024, hop_length=None, duration_seconds=None):
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
        self.top_frequencies = []
        self.notes = []

    def hz_to_note_name(self, hz):
        return librosa.hz_to_note(hz)

    def decompose(self, mags):
        nmf_model = NMF(n_components=self.n_components, solver='mu', beta_loss='itakura-saito', max_iter=600)
        acts = nmf_model.fit_transform(np.transpose(mags))
        bases = nmf_model.components_
        acts = np.transpose(acts)
        return bases, acts

    def compute_rms(self, y):
        return np.sqrt(np.mean(y**2))

    def normalize_audio(self, y, target_rms=0.1):
        rms = self.compute_rms(y)
        if rms > 0:
            y = y * (target_rms / rms)
        return y

    def _make_mags_from_basis_and_activation(self, activation, basis):
        return np.outer(basis, activation)

    def _balance_mags_via_softmask(self, resynthesized_mags, mags_to_mask):
        multiplier = 1 / np.maximum(np.sum(resynthesized_mags, axis=0), 1e-10)
        return multiplier * resynthesized_mags * mags_to_mask

    def _make_complex_matrix_from_mags_and_phases(self, mags, phases):
        return mags * np.exp(1j * phases)

    def _istft(self, complex_stft):
        return librosa.istft(complex_stft, **self.fft_settings)

    def assign_frequency_bins(self):
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)
        octave_edges = [50, 110, 220, 440, 880, 1760, 3520, 7040]
        num_bands = len(octave_edges) - 1
        band_votes = []

        self.top_frequencies = []  # reset před novým výpočtem

        for i, basis in enumerate(self.bases):
            top_indices = np.argsort(basis)[-3:][::-1]
            top_freqs = freqs[top_indices]
            self.top_frequencies.append(top_freqs.tolist())  # uložení top frekvencí

            note_names = [self.hz_to_note_name(f) for f in top_freqs]
            print(f"Component {i} top frequencies:")
            for f, note in zip(top_freqs, note_names):
                print(f"  {f:.2f} Hz ({note})")
            for f in top_freqs:
                for j in range(num_bands):
                    if octave_edges[j] <= f < octave_edges[j + 1]:
                        band_votes.append((i, j))

        vote_matrix = np.zeros((len(self.bases), num_bands))
        for comp_idx, band_idx in band_votes:
            vote_matrix[comp_idx, band_idx] += 1

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
        masks_and_ranges = self.assign_frequency_bins()
        for i, (mask, (low_freq, high_freq)) in enumerate(masks_and_ranges):
            filtered_basis = np.zeros_like(self.bases[i])
            filtered_basis[mask] = self.bases[i][mask]
            self.bases[i] = filtered_basis
            self.highlighted_ranges.append((low_freq, high_freq))
            print(f"Component {i}: Assigned unique band {low_freq:.1f} Hz - {high_freq:.1f} Hz")
            
    def analyse_top_frequencies(self):
        if not self.top_frequencies:
            print("Nejdříve zavolej assign_frequency_bins().")
            return

        print(f"\n\nObsah proměnné print top freq {self.top_frequencies}")

        all_classes = []
        self.notes = []  # reset

        for i, freqs in enumerate(self.top_frequencies):
            midi_notes = librosa.hz_to_midi(freqs)
            midi_notes_rounded = np.round(midi_notes).astype(int)
            midi_classes = (midi_notes_rounded % 12) + 1

            print(f"\nComponent {i}:")
            print(f"  MIDI noty: {midi_notes_rounded}")
            print(f"  Tónové třídy (1–12): {midi_classes}")

            all_classes.extend(midi_classes.tolist())

        # Spočítej výskyt a vyber 3 nejčastější
        counter = Counter(all_classes)
        most_common_classes = [note for note, count in counter.most_common(3)]
        sorted_notes = sorted(most_common_classes)
        print(f"\nNejčastější 3 tónové třídy (nezávisle na oktávě): {sorted_notes}")

        # Výchozí hodnota typu akordu (0 = neznámý)
        chord_code = 0

        # Výpočet intervalů od root noty
        root = sorted_notes[0]
        intervals = [(n - root) % 12 for n in sorted_notes]
        print(f"  Intervaly od rootu {root}: {sorted(intervals)}")

        interval_patterns = {
            1: [0, 4, 7],     # major
            2: [0, 3, 7],     # minor
            3: [0, 3, 6],     # diminished
            4: [0, 2, 7],     # sus2
            5: [0, 5, 7],     # sus4
            6: [0, 4, 8],     # augmented
            7: [0, 4, 6],     # major flat 5
            8: [0, 2, 8],     # sus2♯5
            9: [0, 5, 10],    # quartal
        }

        for code, pattern in interval_patterns.items():
            if sorted(intervals) == pattern:
                chord_code = code
                break

        self.notes = sorted_notes + [chord_code]
        print(f"  → Výstupní struktura self.notes: {self.notes}")


    def resynthesize(self, normalize=True):
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
        plotter = NMFPlotter(self.stft, self.activations, self.bases, self.sr, self.n_fft, self.highlighted_ranges)
        plotter.plot()

    def export_json(self):
        self.exporter.save_to_json()

def main():
    audio_path = "Test/sound/mixdown.wav"
    model = DecomposeNMF(audio_path, n_components=5, n_fft=8192) # 8192, 4096 
    model.apply_filters()
    # model.export_json()
    # model.resynthesize(normalize=True)
    # model.plot()
    model.analyse_top_frequencies()

if __name__ == '__main__':
    main()
