import sys 
import pyaudio 
import numpy as np
import matplotlib.pyplot as plt
import bpm_calc as bpm

class AnalysisOutput:
    def __init__(self, beat: int, base_tone: int, sharp_diminished: bool,
                 durr_moll: bool, rms_mid: float, rms_side: float, atmosphere: float, bpm: int):
        self.beat = beat
        self.bpm = bpm
        # self.base_tone = base_tone
        # self.sharp_diminished = sharp_diminished
        # self.durr_moll = durr_moll
        # self.rms_mid = rms_mid
        # self.rms_side = rms_side
        # self.atmosphere = atmosphere


class AudioAnalysis:
    def __init__(self, rate=16000, frames_per_buffer=None, format_=pyaudio.paInt16, channels=1):
        # Parametry pro záznam
        self.RATE = rate
        self.FRAMES_PER_BUFFER = frames_per_buffer or round(self.RATE / 5)
        self.FORMAT = format_
        self.CHANNELS = channels
        
        # Parametry pro výpočet
        self.signal = np.array([], dtype=np.int16)
        self.samples_per_second = self.RATE // self.FRAMES_PER_BUFFER
        self.max_amplitude = 32767
        self.seconds = 0
        
        # Parametry pro výpočet BPM
        self.peak_times = []
        self.peak_times_index = 0
        self.peak_buffer_index = 0
        
        # Inicializace PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.FRAMES_PER_BUFFER
        )
    
    def process_audio(self):
        print("Začátek nahrávání, ukončení pomocí ctrl+c")
        
        while True:
            try:
                buffer_data = self.stream.read(self.FRAMES_PER_BUFFER)
                self.peak_times, self.peak_times_index, self.peak_buffer_index = bpm.bpm_timing(
                    buffer_data, self.peak_times, self.peak_times_index, self.peak_buffer_index, self.FRAMES_PER_BUFFER
                )
                
                self.signal = np.concatenate((self.signal, np.frombuffer(buffer_data, dtype=np.int16)))
                
                if len(self.signal) >= self.RATE:
                    rms = np.sqrt(np.mean(np.square(self.signal[-self.RATE:])))
                    dB = 20 * np.log10(rms / self.max_amplitude) if rms > 0 else -np.inf
                    
                    # Resetování signálu
                    self.signal = np.array([], dtype=np.int16)
            except KeyboardInterrupt:
                self.cleanup()
    
    def cleanup(self):
        print("\nProgram byl přerušen.")
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        print("Vykonávám závěrečné kroky...")
        sys.exit(0)

if __name__ == "__main__":
    analyzer = AudioAnalysis()
    analyzer.process_audio()
