from metrics_collector import start_collector
import os
import signal

class Benchmark:
    def __init__(self, output_file="metrics_log.jsonl", interval=1.0):
        self.output_file = output_file
        self.interval = interval
        self.process = None

    def start(self):
        if self.process is None:
            self.process = start_collector(self.output_file, self.interval)

    def stop(self):
        if self.process:
            os.kill(self.process.pid, signal.SIGTERM)
            self.process.join()
            self.process = None
