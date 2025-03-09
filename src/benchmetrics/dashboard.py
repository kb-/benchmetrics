import logging
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly_resampler import FigureResampler
import json
import os

benchmark_dashboard = dash.Dash(__name__)
logging.getLogger("benchmetrics.dashboard").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
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

benchmark_dashboard.layout = html.Div(style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'}, children=[
    html.H2("🚀 Real-time Benchmark Metrics Dashboard", style={'textAlign': 'center'}),

    html.Div(style={
        'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap'
    }, children=[
        html.Div(style={'width': '48%', 'minWidth': '400px'}, children=[
            dcc.Graph(id='memory-usage'),
        ]),
        html.Div(style={'width': '48%', 'minWidth': '400px'}, children=[
            dcc.Graph(id='load-percentages'),
        ]),
    ]),

    html.H3("📊 Metrics Summary", style={'textAlign': 'center', 'marginTop': '20px'}),
    html.Table(style={
        'width': '70%', 'margin': '0 auto', 'borderCollapse': 'collapse', 'boxShadow': '0 2px 5px #ccc'
    }, children=[
        html.Thead(html.Tr([
            html.Th("Metric", style={'padding': '10px', 'borderBottom': '2px solid #ddd', 'backgroundColor': '#f0f0f0'}),
            html.Th("Current", style={'padding': '10px', 'borderBottom': '2px solid #ddd', 'backgroundColor': '#f0f0f0'}),
            html.Th("Min", style={'padding': '10px', 'borderBottom': '2px solid #ddd', 'backgroundColor': '#f0f0f0'}),
            html.Th("Max", style={'padding': '10px', 'borderBottom': '2px solid #ddd', 'backgroundColor': '#f0f0f0'}),
        ])),
        html.Tbody(id="metrics-summary")
    ]),

    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

@benchmark_dashboard.callback(
    [Output('memory-usage', 'figure'),
     Output('load-percentages', 'figure'),
     Output('metrics-summary', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):
    metrics = read_metrics()
    timestamps = [t - metrics["timestamp"][0] for t in metrics["timestamp"]] if metrics["timestamp"] else []

    # Memory usage figure
    memory_fig = FigureResampler(go.Figure())
    memory_fig.add_trace(go.Scatter(x=timestamps, y=metrics["ram_usage_gb"], name='RAM Usage (GB)'))
    memory_fig.add_trace(go.Scatter(x=timestamps, y=metrics["swap_usage_gb"], name='Swap Usage (GB)'))
    memory_fig.add_trace(go.Scatter(x=timestamps, y=metrics["gpu_mem_used_gb"], name='GPU VRAM Usage (GB)'))
    memory_fig.update_layout(
        title='Memory Usage (GB)', xaxis=dict(title='Time (s)'), yaxis=dict(title='GB'),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Load percentages figure
    load_fig = FigureResampler(go.Figure())
    load_fig.add_trace(go.Scatter(x=timestamps, y=metrics["cpu_load_percent"], name='CPU Load (%)'))
    load_fig.add_trace(go.Scatter(x=timestamps, y=metrics["gpu_load_percent"], name='GPU Load (%)'))
    load_fig.add_trace(go.Scatter(x=timestamps, y=metrics["gpu_mem_load_percent"], name='GPU Memory Load (%)'))
    load_fig.update_layout(
        title='Load Percentages (%)', xaxis=dict(title='Time (s)'), yaxis=dict(title='%'),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Metrics summary table
    def summarize(data):
        return f"{data[-1]:.2f}", f"{min(data):.2f}", f"{max(data):.2f}"

    summary_rows = []
    if timestamps:
        summary_data = {
            "CPU Load (%)": metrics["cpu_load_percent"],
            "GPU Load (%)": metrics["gpu_load_percent"],
            "GPU Memory Load (%)": metrics["gpu_mem_load_percent"],
            "RAM Usage (GB)": metrics["ram_usage_gb"],
            "Swap Usage (GB)": metrics["swap_usage_gb"],
            "GPU VRAM Usage (GB)": metrics["gpu_mem_used_gb"],
        }

        for metric_name, values in summary_data.items():
            current, min_val, max_val = summarize(values)
            summary_rows.append(html.Tr([
                html.Td(metric_name, style={'padding': '8px', 'borderBottom': '1px solid #ddd'}),
                html.Td(current, style={'padding': '8px', 'textAlign': 'center', 'borderBottom': '1px solid #ddd'}),
                html.Td(min_val, style={'padding': '8px', 'textAlign': 'center', 'borderBottom': '1px solid #ddd'}),
                html.Td(max_val, style={'padding': '8px', 'textAlign': 'center', 'borderBottom': '1px solid #ddd'}),
            ]))

    return memory_fig, load_fig, summary_rows
