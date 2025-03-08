import multiprocessing as mp
import os
import webbrowser
from .metrics_collector import collect_metrics

def run_dashboard():
    from .dashboard import benchmark_dashboard
    benchmark_dashboard.run_server(debug=False, use_reloader=False)

class Benchmark:
    def __init__(self, interval=1.0, output_file="metrics_log.jsonl", dashboard=True):
        self.interval = interval
        self.output_file = output_file
        self.dashboard = dashboard
        self.collector_process = None
        self.dashboard_process = None

    def start(self):
        if self.collector_process is None:
            if os.path.exists(self.output_file):
                os.remove(self.output_file)

            self.collector_process = mp.Process(
                target=collect_metrics,
                args=(self.output_file, self.interval),
                daemon=True
            )
            self.collector_process.start()

        if self.dashboard and self.dashboard_process is None:
            self.dashboard_process = mp.Process(target=run_dashboard, daemon=True)
            self.dashboard_process.start()
            webbrowser.open("http://127.0.0.1:8050")

    def stop(self):
        if self.collector_process and self.collector_process.is_alive():
            self.collector_process.terminate()
            self.collector_process.join()

        if self.dashboard_process and self.dashboard_process.is_alive():
            self.dashboard_process.terminate()
            self.dashboard_process.join()

        self.collector_process = None
        self.dashboard_process = None
