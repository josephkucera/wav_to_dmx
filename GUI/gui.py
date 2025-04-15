import sys
import time
import threading
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QFileDialog,
    QHBoxLayout, QSlider, QGroupBox, QGridLayout, QMessageBox, QComboBox,
    QFrame, QLCDNumber, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QLinearGradient, QMouseEvent, QPixmap, QImage

from AudioClass import AudioPipeline, FileSource
from DmxControll import SceneManager, LightManager, SimulatorManager, Head
from VectorClass import VectorClass

class SimpleColorPicker(QFrame):
    def __init__(self, callback=None):
        super().__init__()
        self.setFixedHeight(50)
        self.setStyleSheet("background: none; border: 1px solid #888;")
        self.callback = callback
        self.color = QColor(255, 255, 255)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, Qt.red)
        gradient.setColorAt(0.16, Qt.magenta)
        gradient.setColorAt(0.33, Qt.blue)
        gradient.setColorAt(0.5, Qt.cyan)
        gradient.setColorAt(0.66, Qt.green)
        gradient.setColorAt(0.83, Qt.yellow)
        gradient.setColorAt(1.0, Qt.red)
        painter.fillRect(self.rect(), gradient)

    def mousePressEvent(self, event: QMouseEvent):
        x_ratio = event.pos().x() / self.width()
        self.color.setHsvF(x_ratio, 1, 1)
        if self.callback:
            self.callback(self.color)
        self.update()

class WaveformPreview(QLabel):
    def __init__(self, audio_pipeline):
        super().__init__()
        self.audio = audio_pipeline
        self.setFixedHeight(200)
        self.setStyleSheet("background-color: black; border: 1px solid #888;")

    def update_waveform(self):
        with self.audio.lock:
            signal = self.audio.recent_signal[-2048:]
        if len(signal) == 0:
            return

        signal = signal / np.max(np.abs(signal))
        w, h = self.width(), self.height()
        image = QImage(w, h, QImage.Format_RGB32)
        image.fill(QColor("black"))
        painter = QPainter(image)
        painter.setPen(QColor("lime"))

        step = max(1, len(signal) // w)
        mid = h // 2
        for i in range(w):
            idx = i * step
            if idx < len(signal):
                val = int(signal[idx] * (h // 2))
                painter.drawLine(i, mid - val, i, mid + val)

        painter.end()
        self.setPixmap(QPixmap.fromImage(image))

class FaderBlock(QVBoxLayout):
    def __init__(self, name, callback=None):
        super().__init__()
        self.label = QLabel(name)
        self.label.setStyleSheet("color: white")
        self.label.setAlignment(Qt.AlignCenter)
        self.lcd = QLCDNumber()
        self.lcd.setFixedHeight(24)
        self.lcd.setFixedWidth(40)
        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(0, 255)
        self.slider.setValue(128)
        self.slider.setMinimumHeight(3)
        self.slider.setStyleSheet("QSlider::groove:vertical { width: 12px; } QSlider::handle:vertical { height: 20px; }")
        self.slider.valueChanged.connect(self.lcd.display)
        if callback:
            self.slider.valueChanged.connect(callback)
        self.setAlignment(Qt.AlignHCenter)
        self.addWidget(self.label)
        self.addWidget(self.lcd, alignment=Qt.AlignCenter)
        self.addWidget(self.slider, stretch=1)

class LightControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio-Light Controller")
        self.setMinimumSize(1400, 800)
        self.set_dark_mode()

        self.audio_file = "Test/sound/davids_ant.wav"
        self.source = FileSource(self.audio_file)
        self.audio = AudioPipeline(self.source)

        try:
            self.manager = LightManager("light_plot.txt", dmx_frequency=42)
        except RuntimeError:
            self.manager = SimulatorManager("light_plot.txt", dmx_frequency=2)

        self.scene = SceneManager(self.manager.light_plot)
        self.vector = VectorClass(scene_manager=self.scene)
        self.selected_color = QColor(255, 255, 255)

        self.start_button = QPushButton("▶ Start")
        self.stop_button = QPushButton("■ Stop")
        self.file_button = QPushButton("📂 Soubor")
        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.file_button)

        self.group_selector = QComboBox()
        self.group_selector.addItems(["bass", "midA", "midB", "midC", "highA", "highB"])
        self.color_picker = SimpleColorPicker(self.on_color_selected)
        combo_color_layout = QHBoxLayout()
        combo_color_layout.addWidget(self.group_selector)
        combo_color_layout.addWidget(self.color_picker, stretch=1)

        self.audio_preview = WaveformPreview(self.audio)
        self.state_label = QLabel()
        self.state_label.setStyleSheet("color: white; padding: 4px; font-family: Consolas")

        scene_grid = QGridLayout()
        scene_buttons = [
            ("🌑\nBlackout", self.run_blackout),
            ("💓\nPulse", lambda: self.scene.pulse_on_beat("bass")),
            ("🥁\nDrums", self.run_on_drums),
            ("🎤\nMusician", self.run_on_musician),
            ("🔀\nShuffle", self.run_shuffle),
            ("🎲\nGroupShuffle", self.run_shuffle_group),
            ("🌫️\nHazer", self.toggle_hazer),
            ("🌊\nWave", self.run_wave_effect)
        ]
        for i, (label, callback) in enumerate(scene_buttons):
            btn = QPushButton(label)
            btn.clicked.connect(callback)
            btn.setFixedSize(100, 100)
            row, col = divmod(i, 4)
            scene_grid.addWidget(btn, row, col)

        scene_group = QGroupBox("Scény")
        scene_group.setLayout(scene_grid)
        scene_group.setStyleSheet("color: white;")

        # Pohyb světla blok
        light_control_group = QGroupBox("Pohyb světla")
        light_control_layout = QVBoxLayout()
        self.light_selector = QComboBox()
        self.light_selector.setMaximumWidth(150)
        self.head_lights = [l for l in self.scene.light_plot.lights if isinstance(l, Head)]
        self.light_selector.addItems([l.name for l in self.head_lights])

        pan = FaderBlock("Pan", self.update_light_movement)
        tilt = FaderBlock("Tilt", self.update_light_movement)
        zoom = FaderBlock("Zoom", self.update_light_zoom)
        self.pan_slider = pan.slider
        self.tilt_slider = tilt.slider
        self.zoom_slider = zoom.slider

        light_faders = QHBoxLayout()
        light_faders.addLayout(pan)
        light_faders.addLayout(tilt)
        light_faders.addLayout(zoom)

        light_control_layout.addWidget(self.light_selector)
        light_control_layout.addLayout(light_faders)
        light_control_group.setLayout(light_control_layout)

        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("LightGUI_BK.png").scaledToWidth(400, Qt.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignCenter)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self.logo)
        right_panel.addStretch()

        self.master_fader = FaderBlock("Master", self.set_dimmer)
        self.strobo_fader = FaderBlock("Strobo")
        self.fade_fader = FaderBlock("Fade")

        fader_row = QHBoxLayout()
        fader_row.addLayout(self.master_fader)
        fader_row.addLayout(self.strobo_fader)
        fader_row.addLayout(self.fade_fader)

        right_panel.addLayout(fader_row)
        right_panel.addWidget(self.state_label)

        left_panel = QVBoxLayout()
        left_panel.addLayout(controls)
        left_panel.addWidget(self.audio_preview)
        left_panel.addLayout(combo_color_layout)
        left_panel.addWidget(scene_group)
        left_panel.addWidget(light_control_group)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_panel, stretch=3)
        main_layout.addLayout(right_panel, stretch=1)
        self.setLayout(main_layout)

        self.start_button.clicked.connect(self.start_audio)
        self.stop_button.clicked.connect(self.stop_audio)
        self.file_button.clicked.connect(self.select_file)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_audio_state)
        self.timer.start(100)

        self.running = False

    def on_color_selected(self, color):
        self.selected_color = color
        self.scene.set_color_for_group(self.get_selected_group(), (color.red(), color.green(), color.blue()))

    def get_selected_group(self):
        return self.group_selector.currentText()

    def set_dark_mode(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        self.setPalette(dark_palette)

    def run_blackout(self):
        self.scene.blackout()

    def run_on_drums(self):
        self.scene.set_movement_for_group("midB", pan=60, tilt=220)

    def run_on_musician(self):
        self.scene.set_movement_for_group("midB", pan=120, tilt=100)

    def run_shuffle(self):
        threading.Thread(target=self._shuffle_lights, daemon=True).start()

    def _shuffle_lights(self):
        mids = ["midA", "midB", "midC"]
        while self.running:
            for group in mids:
                self.scene.set_dim_for_group(group, 255)
                time.sleep(0.3)
                self.scene.set_dim_for_group(group, 0)
                time.sleep(0.1)

    def run_shuffle_group(self):
        threading.Thread(target=self._shuffle_groups, daemon=True).start()

    def _shuffle_groups(self):
        groups = ["midA", "midB", "midC"]
        while self.running:
            for group in groups:
                self.scene.set_dim_all(0)
                self.scene.set_dim_for_group(group, 255)
                time.sleep(0.5)

    def toggle_hazer(self):
        threading.Thread(target=self._hazer_pulse, daemon=True).start()
        
    def set_dimmer(self, value):
        self.scene.set_dim_all(value)


    def _hazer_pulse(self):
        for light in self.scene.get_group_lights("special"):
            if hasattr(light, "set_haze"):
                light.set_haze(255)
        time.sleep(2)
        for light in self.scene.get_group_lights("special"):
            if hasattr(light, "set_haze"):
                light.set_haze(0)

    def run_wave_effect(self):
        threading.Thread(target=self._wave_effect, daemon=True).start()

    def _wave_effect(self):
        mids = self.scene.get_group_lights("mid")
        for light in mids:
            if hasattr(light, 'set_dim'):
                light.set_dim(255)
                time.sleep(0.2)
                light.set_dim(0)

    def update_light_movement(self):
        index = self.light_selector.currentIndex()
        if index >= 0:
            light = self.head_lights[index]
            if hasattr(light, "set_position"):
                light.set_position(self.pan_slider.value(), self.tilt_slider.value())

    def update_light_zoom(self):
        index = self.light_selector.currentIndex()
        if index >= 0:
            light = self.head_lights[index]
            if hasattr(light, "set_zoom"):
                light.set_zoom(self.zoom_slider.value())

    def select_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Vyber zvukový soubor", ".", "WAV Files (*.wav)")
        if filename:
            self.audio.stop()
            if hasattr(self.source, "cleanup"):
                self.source.cleanup()
            self.audio_file = filename
            self.source = FileSource(self.audio_file)
            self.audio = AudioPipeline(self.source)
            self.vector = VectorClass(scene_manager=self.scene)
            self.audio_preview.audio = self.audio
            self.running = False

    def start_audio(self):
        if not self.running:
            self.audio.start()
            self.running = True

    def stop_audio(self):
        if self.running:
            self.audio.stop()
            self.running = False

    def update_audio_state(self):
        with self.audio.lock:
            state = self.audio.state
        self.vector.process_audio_state(state)
        self.audio_preview.update_waveform()
        self.state_label.setText(
            f"AudioState:\nBeat: {state.beat_on_off} | Tóny: {state.freqs} | Akord: {state.chord}"
        )

def run_gui():
    app = QApplication(sys.argv)
    window = LightControlGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_gui()