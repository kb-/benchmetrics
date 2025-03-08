import sys
import time
import numpy as np
import torch
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from benchmetrics import Benchmark
import multiprocessing

multiprocessing.set_start_method('spawn', force=True)

class ComputationThread(QThread):
    finished = pyqtSignal()

    def run(self):
        for i in range(5):
            print(f'Iteration {i+1}/5 running...')
            if torch.cuda.is_available():
                gpu_tensor = torch.randn((5000, 5000), device='cuda')
                for _ in range(5):
                    gpu_result = torch.mm(gpu_tensor, gpu_tensor)
                torch.cuda.synchronize()
                del gpu_tensor, gpu_result

            large_array = np.random.rand(4000, 4000)
            _ = np.linalg.svd(large_array)
            del large_array

            time.sleep(1)
        self.finished.emit()

class ExampleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.benchmark = Benchmark(interval=1.0, dashboard=True)  # corrected parameter
        self.thread = ComputationThread()
        self.thread.finished.connect(self.end_computation)  # corrected method name

    def init_ui(self):
        self.setWindowTitle('PyQt6 Benchmark Example')
        layout = QVBoxLayout()
        self.status_label = QLabel('Status: Idle')
        layout.addWidget(self.status_label)

        self.start_button = QPushButton('Start Heavy Computation')
        self.start_button.clicked.connect(self.run_computation)
        layout.addWidget(self.start_button)
        self.setLayout(layout)

    def run_computation(self):
        self.status_label.setText('Status: Running heavy computation...')
        self.start_button.setEnabled(False)
        self.benchmark.start()

        self.thread = ComputationThread()
        self.thread.finished.connect(self.end_computation)
        self.thread.start()

    def end_computation(self):
        self.benchmark.stop()
        self.status_label.setText('Status: Completed')
        self.start_button.setEnabled(True)

    def closeEvent(self, event):
        self.benchmark.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = ExampleApp()
    example.show()
    sys.exit(app.exec())
