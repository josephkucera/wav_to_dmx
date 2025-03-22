import sys 
import pyaudio 
import numpy as np
import matplotlib.pyplot as plt
import bpm_calc as bpm
import filter as flt


class AudioAnalysis:
    """ Třída na úpravu audio signálu 
        - Vzorkovací frekvence
        - Velikost bufferu (jinak vf/5)
        - Formát ukládání dat (16bit pyaud)
        - počet kanálů (1 resp. mono)
    """
    def __init__(self, rate=44100, frames_per_buffer=None, format_=pyaudio.paInt16, channels=1):
        # Parametry pro záznam upravitelné
        self.RATE = rate
        self.FRAMES_PER_BUFFER = frames_per_buffer or round(self.RATE / 5)
        self.FORMAT = format_
        self.CHANNELS = channels
        
        # Parametry pro výpočet
        self.signal = np.array([], dtype=np.int16)
        self.SignalRms = np.array([], dtype=np.int16)
        self.samples_per_second = self.RATE // self.FRAMES_PER_BUFFER
        self.max_amplitude = 32767
        self.seconds = 0
        self.buffer_data = []
        self.rms = 0
        self.db = 0

        
        # Parametry pro návrat BPM
        self.peak_times = []
        self.peak_boll = 0
        self.bpm =0
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
 
    def filter(self,SignalData, filter_type ='HP', fs= 44100, f1=200, f2=None,Q = 4):
        """Filtrace signálu
           Parametry
        - signal: vstupní signál (numpy array)
        - filter_type: 'HP' pro Horní Propust, 'LP' pro Dolní Propust, 'BP' pro Pásmovou Propust
        - fs: vzorkovací frekvence (Hz)
        - f1: mezní frekvence (Hz) (dolní pokud je BP filtr)
        - f2: horní mezní frekvence (pokud je použitý BP filtr)
        - Q: Kvalita filtru resp. Ntý řád filtru (standardně 4)
        
            -Pokles = Q*6 dB / Oktávu (standardně 24 dB/okt)
        """
        print("filtrace signalu")
        filtered_signal = flt.create_filter(SignalData, filter_type, fs, f1, f2, Q)
        return filtered_signal
        
            

    def BpmCalculator(self, SignalData):
        """ Posílá načtené data na analýzu BPM
            - SignalData: Nezpracovaný signál
            Nejprve signál načte, poté ho vyfiltruje a nakonec zanalyzuje
        """
       # SignalData = self.filter(SignalData, 'LP', self.RATE,200)
        
        self.bpm, self.peak_boll, self.peak_times, self.peak_times_index, self.peak_buffer_index = bpm.bpm_timing(
            SignalData, self.peak_times, self.peak_times_index, self.peak_buffer_index, self.FRAMES_PER_BUFFER
        )

    
    def RmsCalculator(self,SignalData):
        
        self.SignalRms = np.concatenate((self.SignalRms, np.frombuffer(SignalData, dtype=np.int16)))
        
        if len(self.SignalRms) >= self.RATE:
            rms = np.sqrt(np.mean(np.square(self.SignalRms[-self.RATE:])))
            dB = 20 * np.log10(rms / self.max_amplitude) if rms > 0 else -np.inf
            
            self.rms = rms
            self.db = dB
            
            # Resetování signálu
            self.SignalRms = np.array([], dtype=np.int16)

        
    def AudioInput(self):
        """
        Načítá buffer a převádí ho na np.array
        """
        buffer_data = self.stream.read(self.FRAMES_PER_BUFFER) # načte audio ze streamu
        buffer_data = np.frombuffer(buffer_data, dtype=np.int16) # převede signál na np array
        
        return buffer_data
    
    def AudioProcessing(self):
        """Kontrolní funkce, volá nejprve AudioInput a poté posílá načtený signál na jednotlivé analýzy 
        """
        self.signal = self.AudioInput()
        self.BpmCalculator(self.signal)
        self.RmsCalculator(self.signal)
    
    def cleanup(self):
        """Ukončení programu zavře audistream
        """
        print("\nProgram byl přerušen.")
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        print("Vykonávám závěrečné kroky...")
        sys.exit(0)


