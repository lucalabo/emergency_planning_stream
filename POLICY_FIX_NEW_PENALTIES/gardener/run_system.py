import subprocess
import os
import sys
import time
import signal
import re
from mongo_utils import MongoUtils

# === CONFIGURATION ===
INSTANCE_FILE = "instances/small-nd-50-001.lp"
HORIZON = 4
RADIUS = 3
SIZE = 50
TICK_RATE = 3000
INITIALIZATION_DELAY = 10 # Seconds to wait for DPSR to initialize
CUSTOM_LOG_NAME = "size50_horizon4_radius3_freq3"     # Set to a string if you want a specific log name

# Paths for DPSR (as specified by user)
DPSR_JAR = "../DPSR/DP-sr-v1.0.0.jar"
DPSR_PROGRAM = "../DPSR/queries/program/policy_fix.dpsr"
DPSR_CONFIG = "../DPSR/queries/config/policy_fix.yaml"
EXTERNAL_PY = "load_policy.py" # Local to gardener folder
# =====================

def run_system():
    instance_path = os.path.abspath(INSTANCE_FILE)
    instance_name = os.path.basename(instance_path).replace('.lp', '')
    
    if not os.path.exists(instance_path):
        print(f"Error: Instance file not found at {instance_path}")
        sys.exit(1)
        
    # 0. Clear MongoDB collections before starting
    print(f"[*] Clearing MongoDB collections...")
    try:
        MongoUtils().clear_collections()
    except Exception as e:
        print(f"[!] Warning: Could not clear MongoDB: {e}")

    # 1. Precompute Water Policy
    print(f"=== [1/4] Precomputing Water Policy for {instance_name} ===")
    precompute_cmd = [sys.executable, "precompute_water.py", instance_path]
    try:
        subprocess.run(precompute_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during precomputation: {e}")
        sys.exit(1)
        
    # 2. Setup Logging
    if not os.path.exists("log_results"):
        os.makedirs("log_results")
        
    log_filename = CUSTOM_LOG_NAME if CUSTOM_LOG_NAME else f"{instance_name}_h{HORIZON}_r{RADIUS}.log"
    log_path = os.path.join("log_results", log_filename)
    
    # 3. Start DPSR Engine and Simulation
    print(f"=== [2/4] Starting DPSR Engine and Simulation ===")
    
    # DPSR Command
    dpsr_cmd = [
        "java", "-jar", DPSR_JAR,
        "--program=" + DPSR_PROGRAM,
        "--mongodb",
        "--mongodb-config=" + DPSR_CONFIG,
        "--t-unit=sec",
        "--windows-unit=sec",
        "--t-format=sec",
        "--py-script=" + EXTERNAL_PY,
        "--parallelism=2"
    ]
    
    # Simulation Command
    sim_cmd = [
        sys.executable, "stream_gardener.py", instance_path,
        "--horizon", str(HORIZON),
        "--radius", str(RADIUS),
        "--size", str(SIZE),
        "--tick_rate", str(TICK_RATE)
    ]
    
    log_file = open(log_path, "w")
    print(f"[*] Writing DPSR output to {log_path}")
    
    # Start DPSR with process group
    dpsr_proc = subprocess.Popen(
        dpsr_cmd, 
        stdout=log_file, 
        stderr=subprocess.STDOUT, 
        text=True,
        preexec_fn=os.setsid
    )
    
    print(f"[*] Waiting {INITIALIZATION_DELAY} seconds for DPSR to initialize...")
    time.sleep(INITIALIZATION_DELAY)
    
    # Start Simulation
    print(f"[*] Starting Gardener Simulation...")
    sim_proc = subprocess.Popen(sim_cmd)
    
    print("[*] System running... Monitoring log for completion...")
    
    try:
        # Monitor log file for completion atom
        while True:
            time.sleep(2) # Poll every 2 seconds
            
            # Check if simulation finished
            if sim_proc.poll() is not None:
                print("\n[*] Simulation finished or stopped.")
                break
                
            # Check log for positionReached
            try:
                with open(log_path, "r") as f:
                    content = f.read()
                    if "positionReached" in content:
                        print("\n[!] SUCCESS: Position reached!")
                        break
            except Exception:
                pass
            
            # Also check if DPSR is still alive
            if dpsr_proc.poll() is not None:
                print("\n[!] DPSR engine stopped unexpectedly.")
                break
                
    except KeyboardInterrupt:
        print("\nStopping system...")
    finally:
        # Cleanup
        print("[*] Cleaning up processes...")
        # Kill DPSR process group
        try:
            os.killpg(os.getpgid(dpsr_proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
            
        sim_proc.terminate()
        
        try:
            sim_proc.wait(timeout=5)
            dpsr_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sim_proc.kill()
            try:
                os.killpg(os.getpgid(dpsr_proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        
        log_file.close()
        
    # 4. Analyze Results
    print(f"\n=== [3/4] Analyzing Results from {log_path} ===")
    if os.path.exists(log_path):
        analyze_cmd = [sys.executable, "analyze_dpsr_log.py", log_path]
        subprocess.run(analyze_cmd)
    else:
        print(f"[!] Log file not found at {log_path}")
    
    print("\n=== [4/4] Finished ===")

if __name__ == "__main__":
    run_system()

if __name__ == "__main__":
    run_system()
