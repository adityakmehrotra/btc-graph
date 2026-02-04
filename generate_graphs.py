from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


QUERY_FILES = [
    "query_one.txt",
    "query_two.txt",
    "query_three.txt",
    "query_four.txt",
    "query_five.txt",
    "query_six.txt",
    "query_seven.txt",
]

QUERY_LABELS = {
    "query_one.txt": "1",
    "query_two.txt": "2",
    "query_three.txt": "3",
    "query_four.txt": "4",
    "query_five.txt": "5",
    "query_six.txt": "6",
    "query_seven.txt": "7",
}


def _parse_section(
    lines: List[str], start_index: int
) -> Tuple[List[float], float | None, float | None, float | None, float | None]:
    values: List[float] = []
    init_value: float | None = None
    avg = None
    min_val = None
    max_val = None

    idx = start_index
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue

        if line.startswith("CPU Execution Time") or line.startswith("GPU Execution Time"):
            if idx != start_index:
                break

        init_match = re.match(r"^Init:\s*([0-9]*\.?[0-9]+)", line)
        if init_match:
            init_value = float(init_match.group(1))
            idx += 1
            continue

        value_match = re.match(r"^\d+\.\s*([0-9]*\.?[0-9]+)", line)
        if value_match:
            values.append(float(value_match.group(1)))
            idx += 1
            continue

        avg_match = re.match(r"^Average:\s*([0-9]*\.?[0-9]+)", line)
        if avg_match:
            avg = float(avg_match.group(1))
            idx += 1
            continue

        range_match = re.match(r"^Range:\s*\[\s*([0-9]*\.?[0-9]+)\s*,\s*([0-9]*\.?[0-9]+)\s*\]", line)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            idx += 1
            continue

        idx += 1

    return values, avg, min_val, max_val, init_value


def parse_file(file_path: Path) -> Dict[str, Dict[str, float | List[float] | None]]:
    lines = file_path.read_text().splitlines()

    gpu_start = next((i for i, line in enumerate(lines) if line.strip().startswith("GPU Execution Time")), None)
    cpu_start = next((i for i, line in enumerate(lines) if line.strip().startswith("CPU Execution Time")), None)

    if gpu_start is None or cpu_start is None:
        raise ValueError(f"Missing GPU or CPU section in {file_path.name}")

    gpu_values, gpu_avg, gpu_min, gpu_max, gpu_init = _parse_section(lines, gpu_start)
    cpu_values, cpu_avg, cpu_min, cpu_max, cpu_init = _parse_section(lines, cpu_start)

    if gpu_avg is None:
        gpu_avg = sum(gpu_values) / len(gpu_values) if gpu_values else None
    if cpu_avg is None:
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else None

    if gpu_min is None or gpu_max is None:
        if gpu_values:
            gpu_min = min(gpu_values)
            gpu_max = max(gpu_values)

    if cpu_min is None or cpu_max is None:
        if cpu_values:
            cpu_min = min(cpu_values)
            cpu_max = max(cpu_values)

    return {
        "gpu": {
            "values": gpu_values,
            "avg": gpu_avg,
            "min": gpu_min,
            "max": gpu_max,
            "init": gpu_init,
        },
        "cpu": {
            "values": cpu_values,
            "avg": cpu_avg,
            "min": cpu_min,
            "max": cpu_max,
            "init": cpu_init,
        },
    }


def plot_query(file_path: Path, output_dir: Path) -> None:
    data = parse_file(file_path)

    gpu_values = data["gpu"]["values"]
    cpu_values = data["cpu"]["values"]

    if not isinstance(gpu_values, list) or not isinstance(cpu_values, list):
        raise ValueError("Parsed values missing for GPU or CPU")

    max_len = max(len(gpu_values), len(cpu_values))
    x = list(range(1, max_len + 1))

    plt.figure(figsize=(10, 5))
    plt.plot(x[: len(gpu_values)], gpu_values, color="black", label="GPU")
    plt.plot(x[: len(cpu_values)], cpu_values, color="red", label="CPU")
    plt.xlabel("Iteration")
    plt.ylabel("Time (seconds)")

    query_label = QUERY_LABELS.get(file_path.name, file_path.stem)
    plt.title(f"GPU vs CPU Execution Time for Query {query_label}")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.3)
    gpu_init = data["gpu"].get("init")
    cpu_init = data["cpu"].get("init")
    if gpu_init is not None or cpu_init is not None:
        init_lines = []
        if gpu_init is not None:
            init_lines.append(f"GPU Init: {gpu_init:.3f}s")
        if cpu_init is not None:
            init_lines.append(f"CPU Init: {cpu_init:.3f}s")
        plt.text(
            0.02,
            0.98,
            "\n".join(init_lines),
            transform=plt.gca().transAxes,
            va="top",
            ha="left",
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none"},
        )
    plt.tight_layout()

    output_file = output_dir / f"query_{query_label}_gpu_vs_cpu.png"
    plt.savefig(output_file, dpi=200)
    plt.close()

    gpu_avg = data["gpu"]["avg"]
    gpu_min = data["gpu"]["min"]
    gpu_max = data["gpu"]["max"]
    cpu_avg = data["cpu"]["avg"]
    cpu_min = data["cpu"]["min"]
    cpu_max = data["cpu"]["max"]

    print(f"{file_path.name}:")
    print(f"  GPU  avg={gpu_avg:.3f} min={gpu_min:.3f} max={gpu_max:.3f}")
    print(f"  CPU  avg={cpu_avg:.3f} min={cpu_min:.3f} max={cpu_max:.3f}")


def main() -> None:
    script_dir = Path(__file__).resolve().parent

    for file_name in QUERY_FILES:
        file_path = script_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_name}")
        plot_query(file_path, script_dir)


if __name__ == "__main__":
    main()
