import time
from AudioClass import AudioPipeline, FileSource
from DmxControll import SimulatorManager, SceneManager
from VectorClass import VectorClass


if __name__ == "__main__":
    dmx_frequency = 1  # Hz
    sleep_time = 1.0 / dmx_frequency

    # Inicializace zdrojů
    source = FileSource("Test/sound/davids_ant.wav")
    audio = AudioPipeline(source)
    manager = SimulatorManager("light_plot.txt", dmx_frequency=dmx_frequency)
    scene = SceneManager(manager.light_plot)
    vector = VectorClass(scene_manager=scene)  # Předání správného objektu

    try:
        audio.start()

        last_chord = None
        while True:
            time.sleep(sleep_time)

            with audio.lock:
                state = audio.state

            # Debug výstup
            if state.beat_on_off:
                now = time.strftime("%H:%M:%S")
                print(f"[DEBUG] {now} - BEAT ON - BPM: {state.bpm}, dB: {state.db:.1f}, Chord: {state.chord}")
                if state.chord != last_chord:
                    print(f"  → Chord changed to: {state.chord}")
                    last_chord = state.chord

            # Převod stavu na DMX příkazy
            vector.update(state)

    except KeyboardInterrupt:
        print("\nZastavuji...")
    finally:
        audio.stop()
        manager.cleanup()
        if hasattr(source, "cleanup"):
            source.cleanup()
