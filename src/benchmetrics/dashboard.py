import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import json
import os

benchmark_dashboard = dash.Dash(__name__)
LOG_FILE = "metrics_log.jsonl"

def read_metrics():
    data = {
        "timestamp": [],
        "cpu_load_percent": [],
        "ram_usage_gb": [],
        "swap_usage_gb": [],
        "gpu_mem_used_gb": [],
        "gpu_load_percent": [],
        "gpu_mem_load_percent": [],
    }

    if not os.path.exists(LOG_FILE):
        return data

    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                data["timestamp"].append(entry.get("timestamp", 0))
                data["cpu_load_percent"].append(entry.get("cpu_load_percent", 0))
                data["ram_usage_gb"].append(entry.get("ram_usage_mb", 0) / 1024)
                data["swap_usage_gb"].append(entry.get("swap_usage_mb", 0) / 1024)
                data["gpu_mem_used_gb"].append(entry.get("gpu_mem_used_mb", 0) / 1024)
                data["gpu_load_percent"].append(entry.get("gpu_load_percent", 0))
                data["gpu_mem_load_percent"].append(entry.get("gpu_mem_load_percent", 0))
            except json.JSONDecodeError:
                continue
    return data

benchmark_dashboard.layout = html.Div([
    html.H3("Real-time Benchmark Metrics"),
    dcc.Graph(id='memory-usage'),
    dcc.Graph(id='load-percentages'),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

@benchmark_dashboard.callback(
    [Output('memory-usage', 'figure'), Output('load-percentages', 'figure')],
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):
    metrics = read_metrics()
    timestamps = [t - metrics["timestamp"][0] for t in metrics["timestamp"]] if metrics["timestamp"] else []

    memory_fig = go.Figure()
    memory_fig.add_trace(go.Scatter(x=timestamps, y=metrics["ram_usage_gb"], name='RAM Usage (GB)'))
    memory_fig.add_trace(go.Scatter(x=timestamps, y=metrics["swap_usage_gb"], name='Swap Usage (GB)'))
    memory_fig.add_trace(go.Scatter(x=timestamps, y=metrics["gpu_mem_used_gb"], name='GPU VRAM Usage (GB)'))
    memory_fig.update_layout(title='Memory Usage (GB)', xaxis=dict(title='Time (s)'), yaxis=dict(title='GB'))

    load_fig = go.Figure()
    load_fig.add_trace(go.Scatter(x=timestamps, y=metrics["cpu_load_percent"], name='CPU Load (%)'))
    load_fig.add_trace(go.Scatter(x=timestamps, y=metrics["gpu_load_percent"], name='GPU Load (%)'))
    load_fig.add_trace(go.Scatter(x=timestamps, y=metrics["gpu_mem_load_percent"], name='GPU Memory Load (%)'))
    load_fig.update_layout(title='Load Percentages (%)', xaxis=dict(title='Time (s)'), yaxis=dict(title='%'))

    return memory_fig, load_fig
