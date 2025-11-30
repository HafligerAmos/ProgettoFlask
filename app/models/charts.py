import os
from typing import List

import matplotlib.pyplot as plt

plt.switch_backend("Agg")


def _save_chart(fig, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def generate_single_asset_chart(values: List[float], asset_name: str, output_path: str):
    years = list(range(len(values)))
    fig, ax = plt.subplots()
    ax.plot(years, values, marker="o", label=asset_name)
    ax.set_xlabel("Years")
    ax.set_ylabel("Value ($)")
    ax.set_title(f"Value over time - {asset_name}")
    ax.legend()
    _save_chart(fig, output_path)


def generate_portfolio_chart(values: List[float], output_path: str):
    years = list(range(len(values)))
    fig, ax = plt.subplots()
    ax.plot(years, values, color="green", linewidth=2.5)
    ax.set_xlabel("Years")
    ax.set_ylabel("Total Value ($)")
    ax.set_title("Portfolio growth over time")
    _save_chart(fig, output_path)


def generate_multi_asset_chart(series_list: List[List[float]], labels: List[str], output_path: str):
    fig, ax = plt.subplots()
    for values, label in zip(series_list, labels):
        years = list(range(len(values)))
        ax.plot(years, values, marker="o", label=label)
    ax.set_xlabel("Years")
    ax.set_ylabel("Value ($)")
    ax.set_title("Multi-asset comparison")
    ax.legend()
    _save_chart(fig, output_path)
