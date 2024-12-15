import pyaudio
import wave
import matplotlib.pyplot as plt
import numpy as np

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER    
)

print("start recording")

seconds = 5
frames = []

for i in range (0,int(RATE/FRAMES_PER_BUFFER*seconds)):
    data = stream.read(FRAMES_PER_BUFFER)
    frames.append(data)
    
stream.stop_stream()
stream.close()
p.terminate


obj = wave.open("output.wav", "wb")
obj.setnchannels(CHANNELS)
obj.setsampwidth(p.get_sample_size(FORMAT))
obj.setframerate(RATE)
obj.writeframes(b"".join(frames))
obj.close()


obj_out = wave.open("output.wav", "rb")
sample_freq = obj_out.getframerate()
n_samples = obj_out.getnframes()
signal_wave = obj_out.readframes(-1)
obj_out.close()

t_audio = n_samples / sample_freq
print(t_audio)

signal_array = np.frombuffer(signal_wave, dtype=np.int16)

for i in range (0, len(signal_array)):
    if signal_array[i] > 1000 and signal_array[i+1] < signal_array[i] and signal_array[i-1] < signal_array[i]:
        print(f" peak v hodnotě {signal_array[i]} v case {i/len(signal_array)*t_audio}")

    

times = np.linspace(0, t_audio, num=n_samples)

plt.figure(figsize=(15,5))
plt.plot(times,signal_array)
plt.title("Audio signal")
plt.ylabel("Signal Wave")
plt.xlabel("Time (s)")
plt.xlim(0,t_audio)
plt.show()