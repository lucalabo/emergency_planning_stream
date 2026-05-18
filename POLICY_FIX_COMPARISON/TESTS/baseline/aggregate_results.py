#!/usr/bin/env python3
import csv
import re
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).parent

PATTERNS = [
    ("plants_killed",       re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s+plants killed")),
    ("frogs_killed",        re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s+frogs killed")),
    ("steps_taken",         re.compile(r"^\s*(\d+)\s+steps taken")),
    ("avg_time_per_step",   re.compile(r"^\s*([\d.]+)\s+average time per step")),
    ("max_time_per_step",   re.compile(r"^\s*(\d+)\s+max time per step")),
    ("min_time_per_step",   re.compile(r"^\s*(\d+)\s+min time per step")),
    ("startup_time",        re.compile(r"^\s*(\d+)\s+startup time")),
    ("asp_interceptions",   re.compile(r"^\s*(\d+)\s+interceptions from ASP")),
]

FIELDS = [
    "plants_killed", "plants_total",
    "frogs_killed", "frogs_total",
    "steps_taken",
    "avg_time_per_step", "max_time_per_step", "min_time_per_step",
    "startup_time", "asp_interceptions",
]


def parse_stdout(path: Path):
    text = path.read_text(errors="replace")
    tail = "\n".join(text.splitlines()[-30:])
    res = {}
    for line in tail.splitlines():
        for key, pat in PATTERNS:
            m = pat.match(line)
            if not m:
                continue
            if key in ("plants_killed", "frogs_killed"):
                res[key] = int(m.group(1))
                res[key.split("_")[0] + "_total"] = int(m.group(2))
            elif key == "avg_time_per_step":
                res[key] = float(m.group(1))
            else:
                res[key] = int(m.group(1))
            break
    return res if res else None


def write_csv(path: Path, fieldnames, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def run_sort_key(name: str):
    m = re.search(r"\d+", name)
    return int(m.group()) if m else name


def avg_or_blank(vals):
    vals = [v for v in vals if v is not None]
    return mean(vals) if vals else ""


for config_dir in sorted(ROOT.glob("config*")):
    if not config_dir.is_dir():
        continue
    config_avg_rows = []
    for instance_dir in sorted(config_dir.glob("instance*")):
        if not instance_dir.is_dir():
            continue
        run_rows = []
        for run_dir in sorted(instance_dir.glob("run*"), key=lambda p: run_sort_key(p.name)):
            stdout = run_dir / "stdout.log"
            if not stdout.exists():
                continue
            parsed = parse_stdout(stdout)
            if not parsed:
                print(f"WARN: no results parsed in {stdout}")
                continue
            row = {"run": run_dir.name}
            for f in FIELDS:
                row[f] = parsed.get(f, "")
            run_rows.append(row)

        if run_rows:
            write_csv(instance_dir / "runs.csv", ["run"] + FIELDS, run_rows)

        avg_row = {"instance": instance_dir.name, "num_runs": len(run_rows)}
        for f in FIELDS:
            vals = [r[f] for r in run_rows if r[f] != ""]
            avg_row[f] = avg_or_blank(vals)
        config_avg_rows.append(avg_row)

    if config_avg_rows:
        write_csv(config_dir / "averages.csv",
                  ["instance", "num_runs"] + FIELDS, config_avg_rows)

print("done")
