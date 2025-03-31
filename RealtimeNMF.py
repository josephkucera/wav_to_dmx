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
    def __init__(self, audio_path=None, sr=44100, n_components=5, n_fft=1024, hop_length=None):
        self.audio_path = audio_path
        self.sr = sr
        self.n_components = n_components
        self.n_fft = n_fft
        self.hop_length = hop_length or n_fft // 2
        self.fft_settings = {'n_fft': self.n_fft, 'hop_length': self.hop_length}

        self.top_frequencies = []
        self.notes = []
        self.stft = None
        self.original_mags = None
        self.original_phases = None
        self.bases = None
        self.activations = None
        self.highlighted_ranges = []
        self.normalized_components = []

    def hz_to_note_name(self, hz):
        return librosa.hz_to_note(hz)

    def decompose(self, mags):
        nmf_model = NMF(
            n_components=self.n_components,
            solver='mu',
            beta_loss='itakura-saito',
            init='random',
            max_iter=600,
            random_state=0
        )
        acts = nmf_model.fit_transform(mags.T)
        bases = nmf_model.components_
        acts = acts.T
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

        self.top_frequencies = []

        for i, basis in enumerate(self.bases):
            top_indices = np.argsort(basis)[-3:][::-1]
            top_freqs = freqs[top_indices]
            self.top_frequencies.append(top_freqs.tolist())

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

    def analyse_top_frequencies(self):
        if not self.top_frequencies:
            print("Nejdříve zavolej assign_frequency_bins().")
            return

        all_classes = []
        self.notes = []

        for freqs in self.top_frequencies:
            freqs = np.clip(freqs, a_min=1e-6, a_max=None)
            midi_notes = librosa.hz_to_midi(freqs)
            midi_notes = midi_notes[~np.isnan(midi_notes)]
            midi_notes_rounded = np.round(midi_notes).astype(int)
            # midi_classes = midi_classes +1 #offset ladění
            midi_classes = (midi_notes_rounded % 12) + 1
            all_classes.extend(midi_classes.tolist())

        counter = Counter(all_classes)
        most_common_classes = [note for note, count in counter.most_common(3)]
        sorted_notes = sorted(most_common_classes)

        chord_code = 0
        if sorted_notes:
            root = sorted_notes[0]
            intervals = [(n - root) % 12 for n in sorted_notes]

            interval_patterns = {
                1: [0, 4, 7],
                2: [0, 3, 7],
                3: [0, 3, 6],
                4: [0, 2, 7],
                5: [0, 5, 7],
                6: [0, 4, 8],
                7: [0, 4, 6],
                8: [0, 2, 8],
                9: [0, 5, 10],
            }

            for code, pattern in interval_patterns.items():
                if sorted(intervals) == pattern:
                    chord_code = code
                    break

        self.notes = sorted_notes + [chord_code]

    def analyze_buffer(self, signal, normalize=True):
        if signal.dtype == np.int16:
            signal = signal.astype(np.float32) / 32768.0

        self.stft = librosa.stft(signal, **self.fft_settings)
        self.original_mags = np.abs(self.stft)
        self.original_phases = np.angle(self.stft)
        self.bases, self.activations = self.decompose(self.original_mags)

        self.highlighted_ranges = []
        self.top_frequencies = []

        self.assign_frequency_bins()
        self.analyse_top_frequencies()

        resynthesized_mags = [self._make_mags_from_basis_and_activation(self.activations[i], self.bases[i])
                              for i in range(self.n_components)]
        masked_mags = self._balance_mags_via_softmask(resynthesized_mags, self.original_mags)

        if normalize:
            rms_values = []
            for i in range(self.n_components):
                y = self._istft(self._make_complex_matrix_from_mags_and_phases(masked_mags[i], self.original_phases))
                rms_values.append(self.compute_rms(y))
            target_rms = np.mean(rms_values)

            self.normalized_components = []
            for i in range(self.n_components):
                y = self._istft(self._make_complex_matrix_from_mags_and_phases(masked_mags[i], self.original_phases))
                y = self.normalize_audio(y, target_rms)
                self.normalized_components.append(y)
        else:
            self.normalized_components = [
                self._istft(self._make_complex_matrix_from_mags_and_phases(masked_mags[i], self.original_phases))
                for i in range(self.n_components)
            ]

        return self.notes

def main():
    audio_path = "Test/sound/mixdown.wav"
    model = DecomposeNMF(audio_path, n_components=5, n_fft=4096)
    model.apply_filters()
    model.analyse_top_frequencies()
    # model.export_json()
    # model.resynthesize(normalize=True)
    # model.plot()

if __name__ == '__main__':
    main()
