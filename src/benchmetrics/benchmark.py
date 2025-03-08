import multiprocessing as mp
import os
import socket
import time
import webbrowser
import threading
from contextlib import closing
from .metrics_collector import collect_metrics
from .dashboard import benchmark_dashboard

def get_free_port():
    """Finds an available port for the dashboard."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def launch_dashboard(port):
    """Starts the dashboard server."""
    benchmark_dashboard.run_server(debug=False, port=port, use_reloader=False)

def wait_for_dashboard(port, timeout=10):
    """Waits until the dashboard is available before opening it."""
    url = f"http://127.0.0.1:{port}"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                print(f"✅ Dashboard is ready at: {url}")
                webbrowser.open(url, new=2)
                return
        except (OSError, ConnectionRefusedError):
            time.sleep(0.5)  # Wait and retry

    print(f"⚠️ Dashboard did not start within {timeout} seconds.")

class Benchmark:
    def __init__(self, interval=1.0, dashboard=True, auto_open=True):
        self.interval = interval
        self.output_file = "metrics_log.jsonl"
        self.dashboard = dashboard
        self.auto_open = auto_open
        self.port = get_free_port() if dashboard else None
        self.collector_process = None
        self.dashboard_process = None

    def start(self):
        """Starts the benchmark logging and the dashboard."""
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
            self.dashboard_process = mp.Process(
                target=launch_dashboard,
                args=(self.port,),
                daemon=True
            )
            self.dashboard_process.start()

            dashboard_url = f"http://127.0.0.1:{self.port}"
            print(f"🔗 Dashboard running at: {dashboard_url}")

            if self.auto_open:
                threading.Thread(target=wait_for_dashboard, args=(self.port,), daemon=True).start()

    def stop(self):
        """Stops all benchmark-related processes."""
        if self.collector_process and self.collector_process.is_alive():
            self.collector_process.terminate()
            self.collector_process.join()

        if self.dashboard_process and self.dashboard_process.is_alive():
            self.dashboard_process.terminate()
            self.dashboard_process.join()

        self.collector_process = None
        self.dashboard_process = None
