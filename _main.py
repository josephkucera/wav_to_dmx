import time
from AudioClass import AudioPipeline, FileSource
from DmxControll import SceneManager, LightManager
from VectorClass import VectorClass

if __name__ == "__main__":
    dmx_frequency = 42  # Hz
    sleep_time = 1.0 / dmx_frequency

    # Inicializace zdrojů
    source = FileSource("Test/sound/04.wav")
    audio = AudioPipeline(source)
    manager = LightManager("light_plot.txt", dmx_frequency=dmx_frequency)
    scene = SceneManager(manager.light_plot)
    vector = VectorClass(scene_manager=scene)
    scene.load_scene("test02")

    try:
        audio.start()
        while True:
            time.sleep(sleep_time)
            with audio.lock:
                state = audio.state
            vector.process_audio_state(state)

    except KeyboardInterrupt:
        print("\nZastavuji...")
    finally:
        audio.stop()
        manager.cleanup()
        if hasattr(source, "cleanup"):
            source.cleanup()
