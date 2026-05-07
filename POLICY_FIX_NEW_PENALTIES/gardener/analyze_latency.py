import re
import os
import sys
import statistics
import glob

def parse_log_stats(file_path):
    # Regex patterns (from analyze_dpsr_log.py)
    input_regex = re.compile(r"(\d+)\s+Received input for time point:.*ms>\s+(\d+)")
    output_regex = re.compile(r"ANSWER>\s+(\d+)\s+Produced output for time point:.*\(ms\)\s+(\d+)")
    reasoning_regex = re.compile(r"Reasoning\s+Done\s+(\d+(?:,\d+)?)")
    fire_penalty_regex = re.compile(r"onFirePenalty\((\d+)\)")
    mud_penalty_regex = re.compile(r"onMudPenalty\((\d+),(\d+)\)")
    num_plants_regex = re.compile(r"num_plants\((\d+)\)")
    plant_killed_regex = re.compile(r"plantKilled\((\d+),(\d+)\)")
    num_frogs_regex = re.compile(r"num_frogs\((\d+)\)")
    frog_killed_regex = re.compile(r"frogKilled\((\d+)\)")
    step_regex = re.compile(r"step\((\d+)\)")

    input_arrival_times = {}
    latencies = []
    reasoning_times = []
    unique_fire_penalties = set()
    unique_mud_penalties = set()
    killed_plants = set()
    killed_frogs = set()
    total_plants_count = 0
    total_frogs_count = 0
    max_step = 0

    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r') as f:
        for line in f:
            # Reasoning Time
            if "Reasoning" in line and "Done" in line:
                m_res = reasoning_regex.search(line)
                if m_res:
                    t_str = m_res.group(1).replace(',', '.')
                    reasoning_times.append(float(t_str))

            # Input/Output for Latency
            input_match = input_regex.search(line)
            if input_match:
                wall_time_input = int(input_match.group(1))
                logical_ts = int(input_match.group(2))
                if logical_ts not in input_arrival_times:
                    input_arrival_times[logical_ts] = wall_time_input
            
            output_match = output_regex.search(line)
            if output_match:
                wall_time_output = int(output_match.group(1))
                logical_ts = int(output_match.group(2))
                if logical_ts in input_arrival_times:
                    latencies.append(wall_time_output - input_arrival_times[logical_ts])

            # Atoms
            content_match = re.search(r"\[(.*)\]", line)
            if content_match:
                content = content_match.group(1)
                if "Reasoning" in line or "Streaming Atom Evaluation" in line:
                    continue

                m_p = num_plants_regex.search(content)
                if m_p: total_plants_count = max(total_plants_count, int(m_p.group(1)))
                for m in plant_killed_regex.finditer(content): killed_plants.add((m.group(1), m.group(2)))
                m_f = num_frogs_regex.search(content)
                if m_f: total_frogs_count = max(total_frogs_count, int(m_f.group(1)))
                for m in frog_killed_regex.finditer(content): killed_frogs.add(m.group(1))
                m_step = step_regex.search(content)
                if m_step: max_step = max(max_step, int(m_step.group(1)))
                for m in fire_penalty_regex.finditer(content): unique_fire_penalties.add(m.group(1))
                for m in mud_penalty_regex.finditer(content): unique_mud_penalties.add((m.group(1), m.group(2)))

    return {
        "avg_latency": statistics.mean(latencies) if latencies else 0,
        "max_latency": max(latencies) if latencies else 0,
        "avg_reasoning": statistics.mean(reasoning_times) if reasoning_times else 0,
        "max_reasoning": max(reasoning_times) if reasoning_times else 0,
        "steps": max_step,
        "fire_penalties": len(unique_fire_penalties),
        "mud_penalties": len(unique_mud_penalties),
        "plants_killed": len(killed_plants),
        "frogs_killed": len(killed_frogs),
        "total_plants": total_plants_count,
        "total_frogs": total_frogs_count
    }

def main():
    log_dir = "log_results"
    log_files = glob.glob(os.path.join(log_dir, "*.log"))
    
    if not log_files:
        print(f"No log files found in {log_dir}")
        return

    results = []
    
    # Filename pattern: size50_horizon4_radius3_...
    config_regex = re.compile(r"size(\d+)_horizon(\d+)_radius(\d+)")

    for log_file in log_files:
        filename = os.path.basename(log_file)
        match = config_regex.search(filename)
        if not match:
            continue
            
        size = int(match.group(1))
        horizon = int(match.group(2))
        radius = int(match.group(3))
        
        stats = parse_log_stats(log_file)
        if stats:
            stats.update({"size": size, "horizon": horizon, "radius": radius, "file": filename})
            results.append(stats)

    # Sort results for the table
    results.sort(key=lambda x: (x["size"], x["horizon"], x["radius"]))

    # Print Table Header
    header = "| {:>4} | {:>2} | {:>2} | {:>10} | {:>5} | {:>4} | {:>4} | {:>9} | {:>9} |".format(
        "Size", "H", "R", "Avg Lat(ms)", "Steps", "Fire", "Mud", "Plants", "Frogs"
    )
    separator = "|" + "-"*6 + "|" + "-"*4 + "|" + "-"*4 + "|" + "-"*12 + "|" + "-"*7 + "|" + "-"*6 + "|" + "-"*6 + "|" + "-"*11 + "|" + "-"*11 + "|"
    
    print("\n" + "="*83)
    print(" GARDENER SYSTEM PERFORMANCE SUMMARY ")
    print("="*83)
    print(header)
    print(separator)

    for r in results:
        plants_str = "{}/{}".format(r["plants_killed"], r["total_plants"])
        frogs_str = "{}/{}".format(r["frogs_killed"], r["total_frogs"])
        line = "| {:>4} | {:>2} | {:>2} | {:>11.2f} | {:>5} | {:>4} | {:>4} | {:>9} | {:>9} |".format(
            r["size"], r["horizon"], r["radius"], 
            r["avg_latency"],
            r["steps"], r["fire_penalties"], r["mud_penalties"],
            plants_str, frogs_str
        )
        print(line)
    
    print(separator)
    print("Total Logs Analyzed: {}".format(len(results)))
    print("="*83 + "\n")

if __name__ == "__main__":
    main()
