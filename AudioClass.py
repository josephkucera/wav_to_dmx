import threading
import queue
import time
import numpy as np
from dataclasses import dataclass
import librosa
import filter as flt
from RealtimeNMF import DecomposeNMF
import pyaudio
import sys
import datetime


class AudioSource:
    def read_buffer(self):
        raise NotImplementedError("Method read_buffer() must be implemented.")


class MicrophoneSource(AudioSource):
    def __init__(self, rate=44100, frames_per_buffer=None, format_=pyaudio.paInt16, channels=1):
        self.RATE = rate
        self.FRAMES_PER_BUFFER = frames_per_buffer or rate // 5
        self.FORMAT = format_
        self.CHANNELS = channels

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.FRAMES_PER_BUFFER
        )

    def read_buffer(self):
        buffer_data = self.stream.read(self.FRAMES_PER_BUFFER)
        return np.frombuffer(buffer_data, dtype=np.int16)

    def cleanup(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


class FileSource(AudioSource):
    def __init__(self, filepath, rate=44100, buffer_size=None, hop=None):
        self.signal, _ = librosa.load(filepath, sr=rate, mono=True)
        self.rate = rate
        self.buffer_size = buffer_size or rate // 5
        self.hop = hop or self.buffer_size
        self.pointer = 0
        self.sleep_time = self.buffer_size / self.rate

    def read_buffer(self):
        if self.pointer + self.buffer_size >= len(self.signal):
            return None
        frame = self.signal[self.pointer:self.pointer + self.buffer_size]
        self.pointer += self.hop
        frame = np.int16(frame * 32767)
        time.sleep(self.sleep_time)
        return frame


@dataclass
class AudioState:
    rms: float = 0.0
    db: float = -np.inf
    bpm: int = 0
    beat_on_off: bool = False
    freqs: tuple = (0, 0, 0)
    chord: str = ""


class AudioPipeline:
    def __init__(self, source, rate=44100):
        self.source = source
        self.rate = rate
        self.buffer_size = rate // 10

        self.buffer_queue = queue.Queue(maxsize=20)
        self.signal_store = []
        self.recent_signal = np.array([], dtype=np.int16)
        self.state = AudioState()

        self.max_amplitude = 32767
        self.last_beat_time = time.time()
        self.beat_count = 0

        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        self.max_recent_signal_length = self.rate * 4
        self.bpm_ready_event = threading.Event()

        self.nmf_analyzer = DecomposeNMF(sr=self.rate, n_components=5, n_fft=4096)

    def filter(self, signal, filter_type='HP', f1=200, f2=None, Q=4):
        return flt.create_filter(signal, filter_type, self.rate, f1, f2, Q)

    def calculate_rms(self, signal):
        rms = np.sqrt(np.mean(np.square(signal.astype(np.float32))))
        db = 20 * np.log10(rms / self.max_amplitude) if rms > 0 else -np.inf
        with self.lock:
            self.state.rms = rms
            self.state.db = db

    def beat_adjustment(self, signal):
        if self.state.rms < 1.0 or not np.isfinite(self.state.rms):
            return False
        filtered = self.filter(signal, filter_type='BP', f1=20, f2=200, Q=2)
        y = filtered.astype(np.float32)
        if not np.all(np.isfinite(y)):
            return False
        y = y / np.max(np.abs(y))
        onset_env = librosa.onset.onset_strength(y=y, sr=self.rate)
        peaks = librosa.util.peak_pick(
            x=onset_env,
            pre_max=3,
            post_max=3,
            pre_avg=3,
            post_avg=3,
            delta=0.5,
            wait=3
        )
        return len(peaks) > 0

    def calculate_bpm(self):
        y = self.recent_signal.astype(np.float32) / self.max_amplitude
        if len(y) >= self.rate * 4:
            tempo, _ = librosa.beat.beat_track(y=y, sr=self.rate)
            bpm = float(tempo[0]) if isinstance(tempo, (np.ndarray, list)) else float(tempo)
            if bpm > 100:
                bpm /= 2
            with self.lock:
                self.state.bpm = round(bpm)
            self.bpm_ready_event.set()

    def input_loop(self):
        while len(self.recent_signal) < self.rate * 4 and not self.stop_event.is_set():
            buffer = self.source.read_buffer()
            if buffer is None:
                break
            self.recent_signal = np.concatenate((self.recent_signal, buffer))
            time.sleep(self.buffer_size / self.rate)

        while not self.stop_event.is_set():
            buffer = self.source.read_buffer()
            if buffer is None:
                break
            try:
                self.buffer_queue.put(buffer, timeout=0.5)
                self.recent_signal = np.concatenate((self.recent_signal, buffer))
                if len(self.recent_signal) > self.max_recent_signal_length:
                    self.recent_signal = self.recent_signal[-self.max_recent_signal_length:]
            except queue.Full:
                continue
            time.sleep(self.buffer_size / self.rate)

    def beat_analysis_loop(self):
        self.bpm_ready_event.wait()
        self.last_beat_time = time.time()

        while not self.stop_event.is_set():
            now = time.time()
            with self.lock:
                bpm = self.state.bpm

            beat_interval = 60.0 / bpm if bpm > 0 else None
            if beat_interval is None:
                time.sleep(0.01)
                continue

            next_beat_time = self.last_beat_time + beat_interval
            time.sleep(max(0, next_beat_time - now))
            now = time.time()

            buffer = None
            try:
                buffer = self.buffer_queue.get_nowait()
                self.calculate_rms(buffer)
            except queue.Empty:
                pass

            beat_detected = buffer is not None and abs(now - next_beat_time) <= 0.2 and self.beat_adjustment(buffer)
            if beat_detected:
                self.last_beat_time = now
            else:
                self.last_beat_time = next_beat_time

            with self.lock:
                self.state.beat_on_off = True
                self.beat_count += 1

            time.sleep(0.05)
            with self.lock:
                self.state.beat_on_off = False

    def frequency_analysis_loop(self):
        while not self.stop_event.is_set():
            time.sleep(1.0)
            if len(self.recent_signal) >= self.rate:
                data = self.recent_signal[-self.rate:]
                notes = self.nmf_analyzer.analyze_buffer(data)
                with self.lock:
                    if len(notes) >= 3:
                        self.state.freqs = tuple(notes[:3])
                        self.state.chord = str(notes[-1])

    def bpm_analysis_loop(self):
        while not self.stop_event.is_set():
            time.sleep(2.0)
            self.calculate_bpm()

    def start(self):
        self.threads = [
            threading.Thread(target=self.input_loop),
            threading.Thread(target=self.beat_analysis_loop),
            threading.Thread(target=self.frequency_analysis_loop),
            threading.Thread(target=self.bpm_analysis_loop),
        ]
        for t in self.threads:
            t.start()

    def stop(self):
        self.stop_event.set()
        for t in self.threads:
            t.join()


if __name__ == "__main__":
    try:
        source = FileSource("Test/sound/davids_ant.wav")
        pipeline = AudioPipeline(source)
        pipeline.start()

        last_chord = ""
        last_beat_time = time.time()

        while True:
            time.sleep(0.1)
            with pipeline.lock:
                state = pipeline.state
                if state.beat_on_off:
                    last_beat_time = time.time()
                    if state.chord != last_chord:
                        last_chord = state.chord
                elif time.time() - last_beat_time > 2:
                    last_beat_time = time.time()

    except KeyboardInterrupt:
        pipeline.stop()
        if hasattr(source, "cleanup"):
            source.cleanup()
        sys.exit(0)