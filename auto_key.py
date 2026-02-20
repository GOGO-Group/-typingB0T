#!/usr/bin/env python3
"""PyQt6 GUI for auto key presser."""
import sys
import threading
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSpinBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QEvent
try:
    from pynput.keyboard import Controller, Key
except ImportError:
    print("Missing dependency: install with `pip install -r requirements.txt`.")
    sys.exit(1)


class KeyEmitter(QObject):
    """Worker thread for emitting key presses."""
    status_changed = pyqtSignal(str)  # Signal to update UI status

    def __init__(self):
        super().__init__()
        self.controller = Controller()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()   # set = paused

    def _wait_if_paused(self):
        """Block while pause_event is set (app is focused). Return False if stopped."""
        while self.pause_event.is_set():
            if self.stop_event.is_set():
                return False
            time.sleep(0.05)
        return True

    def emit_text(self, text: str, interval: float, newline_mode: str, remove_whitespace: bool):
        """
        Emit text as key presses.
        
        Args:
            text: Text to emit
            interval: Delay between characters (seconds)
            newline_mode: 'enter' or 'shift+enter'
            remove_whitespace: If True, strip leading/trailing whitespace from lines
        """
        self.stop_event.clear()
        self.pause_event.clear()

        # --- 3-second countdown ---
        for s in range(3, 0, -1):
            if self.stop_event.is_set():
                self.status_changed.emit("Cancelled")
                return
            self.status_changed.emit(f"Starting in {s}...")
            time.sleep(1)

        self.status_changed.emit("Emitting...")

        lines = text.split('\n')
        
        if remove_whitespace:
            lines = [line.strip() for line in lines]
        
        total_chars = 0
        start_time = time.time()
        
        try:
            for line_idx, line in enumerate(lines):
                if self.stop_event.is_set():
                    break
                
                # Type characters in the line
                for ch in line:
                    if self.stop_event.is_set():
                        break
                    if not self._wait_if_paused():
                        break
                    self.controller.press(ch)
                    self.controller.release(ch)
                    total_chars += 1
                    time.sleep(interval)
                
                # Handle newline (except on last line)
                if line_idx < len(lines) - 1:
                    if self.stop_event.is_set():
                        break
                    if not self._wait_if_paused():
                        break
                    
                    if newline_mode == 'shift+enter':
                        self.controller.press(Key.shift)
                        self.controller.press(Key.enter)
                        self.controller.release(Key.enter)
                        self.controller.release(Key.shift)
                    else:  # 'enter'
                        self.controller.press(Key.enter)
                        self.controller.release(Key.enter)
                    
                    total_chars += 1
                    time.sleep(interval)
            
            elapsed = time.time() - start_time
            self.status_changed.emit(f"Completed: {total_chars} chars in {elapsed:.1f}s")
        except Exception as e:
            self.status_changed.emit(f"Error: {e}")

    def pause(self):
        """Pause emitting."""
        self.pause_event.set()

    def resume(self):
        """Resume emitting."""
        self.pause_event.clear()

    def stop(self):
        """Signal the worker to stop."""
        self.stop_event.set()


class AutoTypeApp(QMainWindow):
    """Main PyQt6 application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Key Presser")
        self.setGeometry(100, 100, 1000, 600)
        
        self.emitter = None
        self.worker_thread = None
        self.is_emitting = False
        
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout: horizontal (left panel + right content)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel: Settings
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, stretch=1)
        
        # Right panel: Text area and button
        right_layout = QVBoxLayout()
        
        # Label
        label = QLabel("Text to emit:")
        right_layout.addWidget(label)
        
        # Text area
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Paste or type text here...")
        right_layout.addWidget(self.text_area, stretch=1)
        
        # Status label
        self.status_label = QLabel("Ready")
        right_layout.addWidget(self.status_label)
        
        # Start/Stop button
        self.emit_button = QPushButton("Start Emitting")
        self.emit_button.setMinimumHeight(50)
        self.emit_button.clicked.connect(self._on_emit_button_clicked)
        right_layout.addWidget(self.emit_button)
        
        # Add right layout to main layout
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, stretch=3)

    def _create_left_panel(self) -> QWidget:
        """Create the left settings panel."""
        panel_widget = QWidget()
        layout = QVBoxLayout(panel_widget)
        
        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Newline mode
        layout.addWidget(QLabel("Newline mode:"))
        self.newline_combo = QComboBox()
        self.newline_combo.addItems(["Enter", "Shift+Enter"])
        layout.addWidget(self.newline_combo)
        
        # Whitespace handling
        layout.addWidget(QLabel("Whitespace:"))
        self.whitespace_check = QCheckBox("Remove leading/trailing spaces")
        self.whitespace_check.setChecked(False)
        layout.addWidget(self.whitespace_check)
        
        # Typing speed (delay between characters in ms)
        layout.addWidget(QLabel("Character delay (ms):"))
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setMinimum(0)
        self.speed_spinbox.setMaximum(1000)
        self.speed_spinbox.setValue(50)
        self.speed_spinbox.setSuffix(" ms")
        layout.addWidget(self.speed_spinbox)
        
        # Add stretch at the bottom
        layout.addStretch()
        
        return panel_widget

    # --- Focus change: pause when app gains focus, resume when it loses focus ---
    def changeEvent(self, event):
        """Detect window activation/deactivation to pause/resume emitting."""
        if event.type() == QEvent.Type.WindowStateChange or event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                # App gained focus -> pause
                if self.is_emitting and self.emitter:
                    self.emitter.pause()
                    self.status_label.setText("Paused (app focused)")
            else:
                # App lost focus -> resume
                if self.is_emitting and self.emitter:
                    self.emitter.resume()
                    self.status_label.setText("Emitting...")
        super().changeEvent(event)

    def _on_emit_button_clicked(self):
        """Handle start/stop button click."""
        if self.is_emitting:
            # Stop emitting
            self.is_emitting = False
            if self.emitter:
                self.emitter.stop()
            self.emit_button.setText("Start Emitting")
            self.status_label.setText("Stopped")
        else:
            # Start emitting
            text = self.text_area.toPlainText()
            if not text.strip():
                self.status_label.setText("Error: No text provided")
                return
            
            # Get settings
            newline_mode = "shift+enter" if self.newline_combo.currentIndex() == 1 else "enter"
            remove_whitespace = self.whitespace_check.isChecked()
            interval = self.speed_spinbox.value() / 1000.0  # Convert ms to seconds
            
            # Create emitter and worker thread
            self.emitter = KeyEmitter()
            self.emitter.status_changed.connect(self._on_status_changed)
            
            self.worker_thread = threading.Thread(
                target=self.emitter.emit_text,
                args=(text, interval, newline_mode, remove_whitespace),
                daemon=True
            )
            self.worker_thread.start()
            
            self.is_emitting = True
            self.emit_button.setText("Stop Emitting")
            # Status will be updated by the countdown in the worker thread

    def _on_status_changed(self, message: str):
        """Update status label from worker thread signal."""
        self.status_label.setText(message)
        if "Completed" in message or "Error" in message or "Cancelled" in message:
            self.is_emitting = False
            self.emit_button.setText("Start Emitting")


def main():
    app = QApplication(sys.argv)
    window = AutoTypeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
