import time
import psutil
import multiprocessing as mp
from pynvml import (
    nvmlInit, nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo, nvmlDeviceGetUtilizationRates,
    nvmlShutdown
)
import json
import platform

# Import Windows-specific module only if running on Windows
if platform.system() == "Windows":
    import win32pdh


def get_cpu_usage(interval):
    """Measures total CPU usage over the specified interval."""

    if platform.system() == "Windows":
        # Use Windows PDH (Performance Data Helper)
        query_handle = None
        try:
            query_handle = win32pdh.OpenQuery()
            counter_handle = win32pdh.AddCounter(query_handle, r"\Processor Information(_Total)\% Processor Utility")

            # Initial collection
            win32pdh.CollectQueryData(query_handle)
            time.sleep(interval)
            win32pdh.CollectQueryData(query_handle)

            # Retrieve the CPU usage value
            _, cpu_usage = win32pdh.GetFormattedCounterValue(counter_handle, win32pdh.PDH_FMT_LONG)
            return cpu_usage
        except Exception as e:
            print(f"Error in get_cpu_usage (Windows): {e}")
            return 0
        finally:
            if query_handle is not None:
                try:
                    win32pdh.CloseQuery(query_handle)
                except Exception as close_err:
                    print(f"Error closing PDH query: {close_err}")

    else:
        # Linux & macOS alternative using psutil
        return psutil.cpu_percent(interval=interval, percpu=False)


def collect_metrics(output_file, interval):
    """Collects system metrics including CPU, RAM, Swap, and GPU usage."""
    nvmlInit()
    gpu_handle = nvmlDeviceGetHandleByIndex(0)

    with open(output_file, "a") as f:
        while True:
            start_time = time.time()

            # Select the correct CPU monitoring method
            cpu_load = get_cpu_usage(interval)

            # Gather memory usage details
            ram = psutil.virtual_memory().used / (1024**2)  # MB
            swap = psutil.swap_memory().used / (1024**2)    # MB

            # Gather GPU usage metrics
            gpu_mem = nvmlDeviceGetMemoryInfo(gpu_handle)
            gpu_util = nvmlDeviceGetUtilizationRates(gpu_handle)

            data = {
                "timestamp": start_time,
                "cpu_load_percent": cpu_load,
                "ram_usage_mb": ram,
                "swap_usage_mb": swap,
                "gpu_mem_used_mb": gpu_mem.used / (1024**2),
                "gpu_mem_total_mb": gpu_mem.total / (1024**2),
                "gpu_load_percent": gpu_util.gpu,
                "gpu_mem_load_percent": gpu_util.memory
            }

            f.write(json.dumps(data) + "\n")
            f.flush()

            # Ensure the correct interval timing
            elapsed = time.time() - start_time
            if elapsed < interval:
                time.sleep(interval - elapsed)

    nvmlShutdown()


def start_collector(output_file="metrics_log.jsonl", interval=0.25):
    """Starts the metrics collection process as a daemon."""
    collector_process = mp.Process(
        target=collect_metrics,
        args=(output_file, interval),
        daemon=True
    )
    collector_process.start()
    return collector_process


if __name__ == "__main__":
    # Example usage: Start collecting metrics.
    proc = start_collector()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping metrics collection...")
