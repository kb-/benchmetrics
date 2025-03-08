import time
import psutil
import multiprocessing as mp
from pynvml import (
    nvmlInit, nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo, nvmlDeviceGetUtilizationRates,
    nvmlShutdown
)
import json
import os

def collect_metrics(output_file, interval):
    nvmlInit()
    gpu_handle = nvmlDeviceGetHandleByIndex(0)

    # Initial call to set baseline
    psutil.cpu_percent(interval=None)
    time.sleep(0.1)  # Short delay to establish baseline

    with open(output_file, "a") as f:
        while True:
            start_time = time.time()

            # Measure CPU usage over the interval
            cpu_load = psutil.cpu_percent(interval=interval)

            ram = psutil.virtual_memory().used / (1024**2)
            swap = psutil.swap_memory().used / (1024**2)

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

            elapsed = time.time() - start_time
            if elapsed < interval:
                time.sleep(interval - elapsed)

    nvmlShutdown()

def start_collector(output_file="metrics_log.jsonl", interval=1.0):
    collector_process = mp.Process(
        target=collect_metrics,
        args=(output_file, interval),
        daemon=True
    )
    collector_process.start()
    return collector_process
