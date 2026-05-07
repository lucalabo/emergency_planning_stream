import subprocess
import time
import os
import signal
import sys
import re
import statistics
import threading
from mongo_utils import MongoUtils
from analyze_dpsr_log import parse_dpsr_log

# --- CONFIGURATION ---
DPSR_DIR = "../DPSR"
SIM_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_RESULTS_DIR = os.path.join(SIM_DIR, "log_results")
INSTANCE_PATH = "instances/big-nd-200-001.lp"

# Benchmark parameters
GRID_SIZE = 200
# Explicit (radius, horizon) combinations to benchmark
COMBINATIONS = [
    (3, 4),   # radius=3, horizon=4
    (5, 6),   # radius=5, horizon=6
    (5, 8),   # radius=5, horizon=8
]
REPETITIONS = 10
MAX_STEPS = 400
INITIALIZATION_DELAY = 20 # seconds
TICK_RATE = 10000

def run_single_benchmark(radius, horizon, run_id):
    """Runs a single benchmark instance and returns the metrics."""
    # Create a subfolder for the current size
    output_dir = os.path.join(LOG_RESULTS_DIR, f"size{GRID_SIZE}")
    os.makedirs(output_dir, exist_ok=True)
    
    log_name = f"size{GRID_SIZE}_horizon{horizon}_radius{radius}_run{run_id}.log"
    log_path = os.path.join(output_dir, log_name)

    print(f"\n>>> Running: Size={GRID_SIZE}, Radius={radius}, Horizon={horizon}, Run={run_id}")
    print(f">>> Log: {log_path}")

    # 0. Clear MongoDB
    print("[*] Clearing MongoDB...")
    try:
        MongoUtils().clear_collections()
    except Exception as e:
        print(f"[!] Warning: Failed to clear MongoDB: {e}")

    # 1. Start DPSR
    dpsr_cmd = [
        "java", "-jar", "DP-sr-v1.0.0.jar",
        "--program=queries/program/policy_fix.dpsr",
        "--mongodb",
        "--mongodb-config=queries/config/policy_fix.yaml",
        "--t-unit=sec", "--windows-unit=sec", "--t-format=sec",
        "--py-script=queries/external/load_policy.py",
        "--parallelism=2", "--verbose=1"
    ]
    
    log_file = open(log_path, "w")
    proc_dpsr = subprocess.Popen(
        dpsr_cmd,
        cwd=DPSR_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid
    )

    # Global shared state for the monitoring thread
    monitor_state = {"step_count": 0, "stop_flag": False}

    def monitor_and_tee():
        try:
            for line in iter(proc_dpsr.stdout.readline, ''):
                log_file.write(line)
                log_file.flush()
                if "step(" in line:
                    match = re.search(r"step\((\d+)\)", line)
                    if match:
                        monitor_state["step_count"] = int(match.group(1))
                        if monitor_state["step_count"] >= MAX_STEPS:
                            monitor_state["stop_flag"] = True
                
                # Check for 'reached' atom specifically in the atoms list [..., reached, ...]
                if "[" in line and "]" in line:
                    # Look for 'reached' as a word, but not followed by / (to avoid signatures)
                    if re.search(r"\breached\b(?!/)", line) and "streaming atom evaluation" not in line.lower():
                        print(f"\n[*] Goal 'reached' atom detected. Stopping...")
                        monitor_state["stop_flag"] = True
        except Exception as e:
            print(f"[!] Monitor Thread Error: {e}")

    monitor_thread = threading.Thread(target=monitor_and_tee, daemon=True)
    monitor_thread.start()

    # 2. Start initialization delay
    print(f"[*] Waiting {INITIALIZATION_DELAY}s for initialization...")
    time.sleep(INITIALIZATION_DELAY)

    # 3. Start Generator
    gen_cmd = [
        "python3", "stream_gardener.py",
        INSTANCE_PATH,
        "--horizon", str(horizon),
        "--radius", str(radius),
        "--size", str(GRID_SIZE),
        "--tick_rate", str(TICK_RATE)
    ]
    print(f"[*] Starting Generator: {' '.join(gen_cmd)}")
    proc_gen = subprocess.Popen(
        gen_cmd,
        cwd=SIM_DIR,
        preexec_fn=os.setsid
    )

    # 4. Monitor steps
    try:
        while not monitor_state["stop_flag"]:
            if proc_dpsr.poll() is not None:
                print("\n[!] DPSR process terminated unexpectedly.")
                break
            print(f"  [DPSR] Step: {monitor_state['step_count']}/{MAX_STEPS}", end="\r")
            time.sleep(1)
        
        if monitor_state["stop_flag"]:
            print(f"\n[*] Reached step {monitor_state['step_count']}. Stopping...")

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        cleanup(proc_dpsr, proc_gen)
        sys.exit(1)
    finally:
        cleanup(proc_dpsr, proc_gen)
        # Wait for monitor thread to finish reading EOF
        monitor_thread.join(timeout=2)
        log_file.close()

    # 5. Analyze Log
    print(f"[*] Analyzing log: {log_path}")
    metrics = parse_dpsr_log(log_path)
    return metrics

def cleanup(proc_dpsr, proc_gen):
    """Kills process groups."""
    for proc in [proc_gen, proc_dpsr]:
        if proc and proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                time.sleep(1)
                if proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass

def calculate_averages(all_metrics):
    """Averages a list of metric dictionaries."""
    if not all_metrics:
        return {}
    
    avg_metrics = {}
    # Use keys from first dict that has them
    keys = all_metrics[0].keys() if all_metrics else []
    
    for key in keys:
        values = [m[key] for m in all_metrics if m and key in m]
        if values:
            avg_metrics[key] = statistics.mean(values)
        else:
            avg_metrics[key] = 0
            
    return avg_metrics

if __name__ == "__main__":
    start_time = time.time()
    results = {}

    for radius, horizon in COMBINATIONS:
            conf_key = f"R={radius}, H={horizon}"
            print(f"\n" + "="*80)
            print(f"CONFIG: {conf_key}")
            print("="*80)
            
            conf_metrics = []
            for run in range(1, REPETITIONS + 1):
                try:
                    m = run_single_benchmark(radius, horizon, run)
                    if m:
                        conf_metrics.append(m)
                except Exception as e:
                    print(f"[!] Error in run {run}: {e}")
            
            if conf_metrics:
                averages = calculate_averages(conf_metrics)
                results[conf_key] = averages
                print(f"\n>>> AVERAGES for {conf_key}:")
                for k, v in averages.items():
                    print(f"  {k}: {v:.4f}")
            else:
                print(f"[!] No metrics collected for {conf_key}")

    print("\n" + "#"*80)
    print("FINAL SUMMARY (AVERAGES)")
    print("#"*80)
    
    # Save summary in the relevant subfolder
    output_dir = os.path.join(LOG_RESULTS_DIR, f"size{GRID_SIZE}")
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, "summary.txt")
    
    with open(summary_path, "w") as sf:
        sf.write("FINAL SUMMARY (AVERAGES)\n")
        sf.write("="*30 + "\n")
        for conf, avg in results.items():
            print(f"\nConfiguration: {conf}")
            sf.write(f"\nConfiguration: {conf}\n")
            for k, v in avg.items():
                line = f"  {k:25}: {v:.4f}"
                print(line)
                sf.write(line + "\n")
    
    total_duration = (time.time() - start_time) / 60
    print(f"\nTotal duration: {total_duration:.2f} minutes")
    print(f"Final summary saved to: {summary_path}")