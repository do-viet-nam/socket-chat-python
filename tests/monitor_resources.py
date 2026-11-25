
import psutil
import time
import csv
import argparse
from pathlib import Path
from datetime import datetime


def monitor_resources(duration=10, pid=None):
    process = psutil.Process(pid) if pid else None

    output_dir = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "results"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"resources_{timestamp}.csv"

    print("Bat dau giam sat tai nguyen...")

    if process:
        print(f"Process: {process.name()} - PID: {pid}")
        process.cpu_percent(interval=None)
    else:
        print("Che do: Giam sat toan bo may tinh")

    psutil.cpu_percent(interval=None)

    with output_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "elapsed_seconds",
            "cpu_percent",
            "ram_mb",
            "system_ram_percent"
        ])

        start = time.perf_counter()

        for _ in range(duration):
            time.sleep(1)

            elapsed = time.perf_counter() - start
            memory = psutil.virtual_memory()

            if process:
                cpu = process.cpu_percent(interval=None)
                ram = process.memory_info().rss / (1024 ** 2)
            else:
                cpu = psutil.cpu_percent(interval=None)
                ram = memory.used / (1024 ** 2)

            writer.writerow([
                round(elapsed, 2),
                round(cpu, 2),
                round(ram, 2),
                memory.percent
            ])

            print(
                f"Time: {elapsed:.1f}s | "
                f"CPU: {cpu:.1f}% | "
                f"RAM: {ram:.2f} MB | "
                f"System RAM: {memory.percent}%"
            )

    print("\nHoan thanh giam sat!")
    print(f"Ket qua da luu tai: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--duration",
        type=int,
        default=10
    )

    parser.add_argument(
        "--pid",
        type=int,
        default=None
    )

    args = parser.parse_args()

    if args.duration <= 0:
        parser.error("Duration phai lon hon 0")

    monitor_resources(args.duration, args.pid)
