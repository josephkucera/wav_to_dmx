import librosa
import numpy as np
from RealtimeNMF import DecomposeNMF
import time

def simulate_realtime_analysis(audio_path, buffer_size=44100, hop=22050, sr=44100, rms_threshold=0.0005):
    # Načti celý zvuk jako mono a přepočítej na požadovaný sample rate
    signal, file_sr = librosa.load(audio_path, sr=sr, mono=True)
    duration = len(signal) / sr
    print(f"Načten zvuk: {audio_path}, délka: {duration:.2f} s, samplerate: {sr} Hz")

    nmf = DecomposeNMF(sr=sr, n_components=5, n_fft=2048)

    for i in range(0, len(signal) - buffer_size, hop):
        start_time = time.time()
        frame = signal[i:i + buffer_size]

        rms = np.sqrt(np.mean(frame**2))
        t = i / sr

        if rms < rms_threshold:
            print(f"⏸ Frame {i//hop} ({t:.2f}s): ticho (RMS = {rms:.6f}), přeskakuji... ")
            continue

        notes = nmf.analyze_buffer(frame, normalize=True)
        end_time = time.time()
        print(f"▶ Frame {i//hop} ({t:.2f}s): {notes}")
        print(f"\n   ⏱ Analýza trvala {end_time - start_time:.2f} s")
        
    
        
if __name__ == "__main__":
    simulate_realtime_analysis("Test/sound/davids_ant.wav")