import sys
import time
import numpy as np
import torch
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from benchmetrics import Benchmark


class ComputationThread(QThread):
    finished = pyqtSignal()

    def run(self):
        # Actual heavy computation to utilize CPU, RAM, and GPU (if available)
        for i in range(5):
            print(f'Iteration {i+1}/5 running...')
            # Heavy GPU computation (if GPU available)
            if torch.cuda.is_available():
                gpu_tensor = torch.randn((10000, 10000), device='cuda')
                for _ in range(10):
                    gpu_result = torch.mm(gpu_tensor, gpu_tensor)
                torch.cuda.synchronize()
                del gpu_tensor, gpu_result

            # Heavy CPU and RAM usage
            large_array = np.random.rand(5000, 5000)
            _ = np.linalg.svd(large_array)
            del large_array

            time.sleep(1)

        self.finished.emit()


class ExampleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.benchmark = Benchmark(interval=0.5)
        self.thread = ComputationThread()
        self.thread.finished.connect(self.computation_finished)

    def init_ui(self):
        self.setWindowTitle('PyQt6 Benchmark Example')
        layout = QVBoxLayout()

        self.status_label = QLabel('Status: Idle')
        layout.addWidget(self.status_label)

        self.start_button = QPushButton('Start Heavy Computation')
        self.start_button.clicked.connect(self.run_heavy_computation)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def run_heavy_computation(self):
        self.status_label.setText('Status: Running heavy computation...')
        self.benchmark.start()
        self.start_button.setEnabled(False)
        self.thread.start()

    def computation_finished(self):
        self.benchmark.stop()
        self.status_label.setText('Status: Completed')
        self.start_button.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = ExampleApp()
    example.show()
    sys.exit(app.exec())