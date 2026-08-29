import argparse
import re
import time as time_module
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

CASE_DIR = Path("/home/mridul_joshi/OpenFOAM/mridul_joshi-9/run/bubble_sim")
DEFAULT_POST_PROCESSING_DIR = CASE_DIR / "postProcessing" / "bubbleAirVelocity"

def read_velocity_dat(dat_file):
    """Read time and the z component from one volFieldValue.dat file."""
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    values = []

    for line in dat_file.read_text().splitlines():
        scalar_match = re.search(
            rf"^\s*({number})\s+({number})\s*$", line)
        vector_match = re.search(
            rf"^\s*({number})\s*\(\s*({number})\s+({number})\s+({number})\s*\)\s*$",
            line)

        if scalar_match:
            values.append((float(scalar_match.group(1)),
                           float(scalar_match.group(2))))
        elif vector_match:
            values.append((float(vector_match.group(1)),
                           float(vector_match.group(4))))

    return values

def read_all_results(post_processing_dir):
    """Read all timestep data files and return sorted time and Uz arrays."""
    results = {}
    dat_files = sorted(post_processing_dir.glob("*/volFieldValue.dat"),
                       key=lambda path: float(path.parent.name))

    for dat_file in dat_files:
        for current_time, uz in read_velocity_dat(dat_file):
            results[current_time] = uz

    if not results:
        return np.array([]), np.array([])

    times = np.array(sorted(results))
    uz_values = np.array([results[current_time] for current_time in times])
    return times, uz_values

def save_results(times, uz_values):
    """Write the CSV table and velocity plot."""
    np.savetxt(CASE_DIR / "bubble_velocity.csv",
               np.column_stack((times, uz_values)), delimiter=",",
               header="time_s,Uz_m_per_s", comments="")

    fig, axis = plt.subplots(figsize=(9, 5))
    axis.plot(times, uz_values, "b-o", markersize=3, label="Uz")
    axis.axhline(0, color="k", linestyle="--", alpha=0.5)
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Vertical velocity Uz (m/s)")
    axis.set_title("Bubble-region Vertical Velocity vs Time")
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.tight_layout()
    fig.savefig(CASE_DIR / "bubble_velocity_plot.png", dpi=150)
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(
        description="Plot Uz from OpenFOAM volFieldValue .dat files")
    parser.add_argument("--watch", action="store_true",
                        help="keep checking for new post-processing files")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="seconds between checks in watch mode")
    parser.add_argument("--post-processing-dir", type=Path,
                        default=DEFAULT_POST_PROCESSING_DIR,
                        help="directory containing timestep subdirectories")
    args = parser.parse_args()
    printed_times = set()

    while True:
        times, uz_values = read_all_results(args.post_processing_dir)
        if times.size:
            save_results(times, uz_values)
            for current_time, uz in zip(times, uz_values):
                if current_time not in printed_times:
                    print(f"Time {current_time:.3f} s: Uz = {uz:.6f} m/s")
                    printed_times.add(current_time)
            print(f"Updated plot with {len(times)} timesteps; latest time = "
                  f"{times[-1]:.6f} s")
        else:
            print(f"No volFieldValue.dat files found in {args.post_processing_dir}")

        if not args.watch:
            break
        time_module.sleep(args.interval)

if __name__ == "__main__":
    main()