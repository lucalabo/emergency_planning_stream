import re
import sys
import statistics

def parse_dpsr_log(file_path):
    times = []
    
    # Sets to track unique entities across the entire stream
    all_plants = set()
    killed_plants = set()
    killed_frogs = set()
    total_frogs_count = 0
    
    steps_count = 0

    input_arrival_times = {}
    latencies = []

    # Regex patterns
    # [INFO][1765282194073] ... Received input for time point: ... ms> 1765282193000
    # Updated Regex patterns for new log format
    # 1765282194073 Received input for time point: ... ms> 1765282193000
    input_regex = re.compile(r"(\d+)\s+Received input for time point:.*ms>\s+(\d+)")
    
    # ANSWER> 1765282195964 Produced output for time point: ... (ms) 1765282193000
    output_regex = re.compile(r"ANSWER>\s+(\d+)\s+Produced output for time point:.*\(ms\)\s+(\d+)")
    
    # Regex for Reasoning Time
    # 1765285219192	DLV2	0 ... Reasoning	Done	12,172092
    reasoning_regex = re.compile(r"Reasoning\s+Done\s+(\d+(?:,\d+)?)")

    reasoning_times = []

    # Patterns for atoms
    num_plants_regex = re.compile(r"num_plants\((\d+)\)")
    plant_killed_regex = re.compile(r"plantKilled\((\d+),(\d+)\)")
    num_frogs_regex = re.compile(r"num_frogs\((\d+)\)")
    frog_killed_regex = re.compile(r"frogKilled\((\d+)\)")
    step_regex = re.compile(r"step\((\d+)\)")
    
    max_step = 0
    total_plants_count = 0
    
    with open(file_path, 'r') as f:
        for line in f:
            # Stop parsing if goal reached
            # ... (omitted for brevity in replacement, but kept in file)
            # Parse Reasoning Time
            if "Reasoning" in line and "Done" in line:
                m_res = reasoning_regex.search(line)
                if m_res:
                    t_str = m_res.group(1).replace(',', '.')
                    reasoning_times.append(float(t_str))

            # Stop parsing if goal reached
            # Use word boundary to match 'positionReached' atom but NOT 'positionReached/0' signature
            if re.search(r"\breached\b(?!/)", line) and not '"YESSSSSSSS"' in line and "Streaming Atom Evaluation" not in line: 
                 break
            else:
                 pass
            
            # Parse Input Arrival Time
            input_match = input_regex.search(line)
            if input_match:
                wall_time_input = int(input_match.group(1))
                logical_ts = int(input_match.group(2))
                # print(f"DEBUG: Found Input - Wall: {wall_time_input}, Logical: {logical_ts}")
                if logical_ts not in input_arrival_times:
                    input_arrival_times[logical_ts] = wall_time_input
            
            # Parse Output Production Time and calculate latency directly from this line
            output_match = output_regex.search(line)
            if output_match:
                wall_time_output = int(output_match.group(1))
                logical_ts = int(output_match.group(2))
                
                # Calculate latency as Output Wall Time - Input Wall Time (Processing Duration)
                if logical_ts in input_arrival_times:
                    latency = wall_time_output - input_arrival_times[logical_ts]
                    latencies.append(latency)

            
            # 2. Parse Atoms from ANSWER> lines (lines starting with ANSWER> but having content)
            # The line format is: ANSWER> 1765... Produced ...
            # AND THEN the next line has atoms?
            # Looking at the log provided:
            # ANSWER> 1765282195964 Produced output for time point: ...
            # 1765282193000	[num_frogs(23), ... step(0)]
            # So the atoms are on the line FOLLOWING the ANSWER> header?
            # OR sometimes on the same line?
            # In the provided log (lines 101, 105, 108 etc of the log file view):
            # ANSWER> 1765281597000 [num_frogs...] 
            # Wait, the log lines 41, 48 show "ANSWER> 1765... [atoms]" directly.
            # But line 90-91 in my previous thought was analyzing the verbose output "Produced output...".
            # The LOG VIEW provided shows: 
            # 41: ANSWER> 1765281587000 [num_frogs(23)...] 
            # This line DOES NOT have "Produced output...".
            # BUT line 101 says `ANSWER> 1765281597000 [num_frogs...]`
            
            # However, the user also provided a snippet:
            # `ANSWER> 1765282195964 Produced output for time point: ...`
            # `1765282193000 [num_frogs...]`
            # It seems there are TWO formats or lines depending on flags.
            # The user asked to check `--verbose=1`.
            # In `--verbose=1` (Step 951):
            # `ANSWER> 1765282195964 Produced output for time point: ...`
            # `1765282193000 [num_frogs(23)...]`
            
            # The parsing logic for ATOMS currently looks at `line.startswith("ANSWER>")`.
            # If the log lines are split, we need to handle that.
            # Let's handle both:
            # 1. `ANSWER> TS [atoms]`
            # 2. `TS [atoms]` (if following an ANSWER> Produced line)
            
            # Regex for atoms content: `\[(.*)\]`
            
            content_match = re.search(r"\[(.*)\]", line)
            if content_match:
                content = content_match.group(1)
                
                # Filter out debug/profiling lines that might contain atom-like text or just confuse stats
                if "Reasoning" in line or "Streaming Atom Evaluation" in line:
                    continue

                # Proceed if it looks like an atom line (typically starts with a timestamp in the new format, or ANSWER>)
                # Since we filtered out the debug lines, we can assume lines with [...] are relevant if they match our patterns.
                if True:

                    # This is likely an atom line
                    
                    # Track total plants count
                    m_p = num_plants_regex.search(content)
                    if m_p:
                        total_plants_count = max(total_plants_count, int(m_p.group(1)))
                        
                    for m in plant_killed_regex.finditer(content):
                        killed_plants.add((m.group(1), m.group(2)))

                    m_f = num_frogs_regex.search(content)
                    if m_f:
                        total_frogs_count = max(total_frogs_count, int(m_f.group(1)))
                    
                    for m in frog_killed_regex.finditer(content):
                        killed_frogs.add(m.group(1))

                    m_step = step_regex.search(content)
                    if m_step:
                        current_step = int(m_step.group(1))
                        if current_step > max_step:
                            max_step = current_step
                            
                    if 'positionReached' in content: 
                         # Goal reached, stop/cut parsing here as requested
                         break

    if not latencies:
        print("No latency data found (check input/output regex match).")
        avg_time = 0
        max_time = 0
        min_time = 0
    else:
        # Latencies are already in ms
        avg_time = statistics.mean(latencies)
        max_time = max(latencies)
        min_time = min(latencies)
        
    avg_reasoning = 0
    max_reasoning = 0
    if reasoning_times:
        avg_reasoning = statistics.mean(reasoning_times)
        max_reasoning = max(reasoning_times)

    metrics = {
        "killed_plants": len(killed_plants),
        "total_plants": total_plants_count,
        "killed_frogs": len(killed_frogs),
        "total_frogs": total_frogs_count,
        "steps_taken": max_step,
        "avg_time_per_step": avg_time,
        "max_time_per_step": max_time,
        "min_time_per_step": min_time,
        "avg_reasoning_time": avg_reasoning,
        "max_reasoning_time": max_reasoning
    }

    # Print Report matching requested format
    print(f"{metrics['killed_plants']:03d} / {metrics['total_plants']:03d} plants killed")
    print(f"{metrics['killed_frogs']:03d} / {metrics['total_frogs']:03d} frogs killed")
    print(f"{metrics['steps_taken']} steps taken")
    print(f"{metrics['avg_time_per_step']:.6f} average time per step (latency)")
    print(f"{metrics['max_time_per_step']:.0f} max time per step (latency)")
    print(f"{metrics['min_time_per_step']:.0f} min time per step (latency)")
    print(f"{metrics['avg_reasoning_time']:.6f} s average reasoning time")
    print(f"{metrics['max_reasoning_time']:.6f} s max reasoning time")

    return metrics

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_dpsr_log.py <path_to_log_file>")
        sys.exit(1)
    
    parse_dpsr_log(sys.argv[1])
