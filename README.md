# 🌿 Gardener — Stream Reasoning Benchmark Suite

This guide covers **both experimental variants** of the Gardener system:

| Variant | Folder | Description |
|---|---|---|
| **Baseline** | `POLICY_FIX_COMPARISON/gardener/` | Standard policy-fix system, no terrain penalties |
| **Temporal Norms** | `POLICY_FIX_NEW_PENALTIES/` | Extended version with mud, oil, fire, and water temporal norm penalties |

Both variants share the same runtime infrastructure (MongoDB, DPSR engine, `stream_gardener.py`). The only difference is in the **one-time preparation** step (§4) and in the ASP program loaded by the DPSR engine. Everything else in this guide applies to both.

---

## 📋 Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [MongoDB — ReplicaSet Setup](#3-mongodb--replicaset-setup)
4. [One-Time Preparation](#4-one-time-preparation)
5. [Running a Single Experiment](#5-running-a-single-experiment)
6. [Running the Full Benchmark Suite](#6-running-the-full-benchmark-suite)
7. [Analyzing Results](#7-analyzing-results)
8. [Saving & Replaying Simulations](#8-saving--replaying-simulations)
9. [MongoDB Schema Reference](#9-mongodb-schema-reference)
10. [Changing Grid Size — Policy File Alignment](#10-changing-grid-size--policy-file-alignment)
11. [Creating New Instances](#11-creating-new-instances)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        GARDENER SYSTEM                       │
│                                                              │
│  ┌──────────────────┐    MongoDB (ReplicaSet)    ┌────────┐  │
│  │  stream_gardener │ ──── input_stream ──────►  │  DPSR  │  │
│  │    (Python Sim)  │                            │ Engine │  │
│  └──────────────────┘                            └────────┘  │
│           │                                                  │
│    log_results/                                              │
│    saved_simulations/                                        │
└───────────────────────────────────────────────────────────── ┘
```

The system is made up of three main components:

| Component | File | Role |
|---|---|---|
| **Simulator** | `stream_gardener.py` + `stream_game.py` | Runs the Gardener game, streams state to MongoDB at each tick |
| **Reasoner** | `DP-sr-v1.0.0.jar` (DPSR engine) | Reads state from MongoDB, runs ASP reasoning, writes actions back |
| **Shared Bus** | MongoDB `gardener_db` | Decoupled communication via `input_stream` / `output_stream` collections |

The simulator sends the full environment state (player, target, walls, frogs, plants) on first tick, then only dynamic data (frogs, plants) on subsequent ticks. The reasoner consumes this stream and computes the best action via ASP.

---

## 2. Prerequisites

Make sure the following are installed and available in your `PATH`:

| Requirement | Version | Notes |
|---|---|---|
| **Python** | ≥ 3.9 | `python3` |
| **Java** | ≥ 11 | Required to run `DP-sr-v1.0.0.jar` |
| **MongoDB** | ≥ 5.0 | Must be configured as a **ReplicaSet** (see §3) |
| **pymongo** | any | `pip install pymongo` |

Verify your setup:

```bash
python3 --version
java -version
mongosh --eval "rs.status()"
```

---

## 3. MongoDB — ReplicaSet Setup

> ⚠️ **This is a hard requirement.** The DPSR engine uses MongoDB **change streams**, which are only available on ReplicaSet or sharded cluster deployments. A standalone MongoDB instance will **not** work.

### 3.1 — Initialize a Single-Node ReplicaSet (one-time)

If you are running MongoDB locally for development, a single-node ReplicaSet is sufficient.

**Step 1 — Edit your MongoDB configuration** (`/etc/mongod.conf` or equivalent):

```yaml
replication:
  replSetName: "rs0"
```

**Step 2 — Restart MongoDB:**

```bash
sudo systemctl restart mongod
```

**Step 3 — Initialize the ReplicaSet** (run once, inside `mongosh`):

```js
mongosh
> rs.initiate({
    _id: "rs0",
    members: [{ _id: 0, host: "localhost:27017" }]
  })
```

**Step 4 — Verify:**

```js
> rs.status()
// You should see "stateStr" : "PRIMARY"
```

### 3.2 — Connection String

The system connects to MongoDB using the default URI `mongodb://localhost:27017/` and the database `gardener_db`. No additional configuration is required — the `MongoUtils` class handles everything automatically.

---

## 4. One-Time Preparation

The preparation steps differ slightly between the two variants.

---

### 4a. Baseline variant (`POLICY_FIX_COMPARISON`)

Export the pre-trained navigation policy from its binary `.pkl` format to a portable JSON that the DPSR engine can read via `load_policy.py`.

```bash
# From the gardener/ directory
python3 export_policy.py <instance_name>

# Example:
python3 export_policy.py big-nd-200-001
```

This creates `instances/learning/big-nd-200-001.json` containing the full Q-table and parameters. **Run once per instance.**

---

### 4b. Temporal Norms variant (`POLICY_FIX_NEW_PENALTIES`)

This variant introduces terrain-based temporal norm penalties (mud, oil, fire) and a guidance mechanism that steers the agent toward water when muddy. Two preparation steps are required:

#### Step 1 — Export the navigation policy (same as baseline)

```bash
python3 export_policy.py big-nd-200-001
```

#### Step 2 — Precompute terrain properties and the water-seeking policy

```bash
# From the POLICY_FIX_NEW_PENALTIES/ directory
python3 precompute_water.py instances/big-nd-200-001.lp
```

**What this script does — in detail:**

1. **Reads the instance** (grid size, walls, player start, target, frogs, plants).

2. **Randomly assigns terrain properties** to free cells (cells not occupied by walls, player, target, plants or frogs), using the following distribution:

   | Terrain type | Coverage |
   |---|---|
   | 🔵 Water | 10% of total cells |
   | 🟫 Mud | 5% of total cells |
   | ⚫ Oil | 5% of total cells |
   | 🔥 Fire | 5% of total cells |

   The assignment is random at each run of the script, so repeated calls will produce different maps. The result is **written back into the `.lp` instance file** (via `inst.save()`), making the terrain layout persistent for all subsequent runs.

3. **Computes the water-seeking policy** via a multi-source BFS starting simultaneously from every water cell. For every reachable cell `(c, r)` and every action `a ∈ {0,1,2,3}`, the Q-value is defined as:

   ```
   Q(s, a) = −distance(next_state, nearest_water_cell)
   ```

   A higher (less negative) Q-value means the action leads closer to water. Invalid moves (walls or out-of-bounds) receive a penalty of `−9999`.

4. **Saves the water policy** as a JSON file next to the instance:

   ```
   instances/big-nd-200-001.water.json
   ```

   The JSON has the same structure as the navigation policy (`states` + `q_table`) and is consumed by the DPSR engine whenever the active temporal norm requires the agent to seek water.

> ⚠️ **Run `precompute_water.py` before any benchmark** in this variant. If the `.water.json` file is missing or stale (e.g. the instance was regenerated), the water-seeking norm will not be able to guide the agent correctly.

> 🔁 **Terrain is re-randomized every time** `precompute_water.py` is called. To keep a fixed map across multiple benchmark runs, call it once and do not call it again until you intentionally want a new layout.

---

## 5. Running a Single Experiment

A single run requires launching **two processes in parallel**, one in each terminal.

### 5.1 — Parameters

| Parameter | Flag | Default | Description |
|---|---|---|---|
| Instance file | positional | — | Path to the `.lp` instance (e.g. `instances/big-nd-200-001.lp`) |
| Grid size | `--size` | `30` | Size of the environment grid (e.g. `200` for a 200×200 grid) |
| Horizon | `--horizon` | `5` | ASP reasoning horizon |
| Radius | `--radius` | `6` | ASP sensing radius |
| Tick rate | `--tick_rate` | `1000` | Simulation tick rate in milliseconds |

### 5.2 — Launch Sequence

> ⚡ Always start the **DPSR engine first** and wait ~20 seconds for it to initialize before launching the simulator.

**Terminal 1 — Start the DPSR Reasoner** (from the `DPSR/` directory):

```bash
cd ../DPSR

java -jar DP-sr-v1.0.0.jar \
  --program=queries/program/policy_fix.dpsr \
  --mongodb \
  --mongodb-config=queries/config/policy_fix.yaml \
  --t-unit=sec --windows-unit=sec --t-format=sec \
  --py-script=queries/external/load_policy.py \
  --parallelism=2 --verbose=1 \
  | tee ../gardener/log_results/size200_horizon6_radius3.log
```

**Wait ~20 seconds** until initialization messages stop appearing, then:

**Terminal 2 — Start the Simulator** (from the `gardener/` directory):

```bash
cd gardener/

python3 stream_gardener.py instances/big-nd-200-001.lp \
  --size 200 \
  --horizon 6 \
  --radius 3 \
  --tick_rate 1000
```

### 5.3 — Stopping a Run

The run will stop automatically when:
- The agent reaches the **target** (`reached` atom appears in the output), or
- The maximum number of steps is exceeded.

You can also stop it manually with `Ctrl+C` in either terminal.

---

## 6. Running the Full Benchmark Suite

The `run_benchmarks.py` script automates the entire pipeline: it launches the DPSR engine, waits for initialization, starts the simulator, monitors progress, stops after the configured number of steps, analyzes logs, and repeats for every configured combination.

### 6.1 — Configuration

All benchmark parameters are defined at the top of `run_benchmarks.py`:

```python
# Path to instance file (relative to gardener/)
INSTANCE_PATH = "instances/big-nd-200-001.lp"

# Grid size
GRID_SIZE = 200

# (radius, horizon) pairs to benchmark
COMBINATIONS = [
    (3, 4),   # radius=3, horizon=4
    (5, 6),   # radius=5, horizon=6
    (5, 8),   # radius=5, horizon=8
]

REPETITIONS       = 10     # Number of repetitions per combination
MAX_STEPS         = 400    # Stop after this many reasoning steps
INITIALIZATION_DELAY = 20  # Seconds to wait for DPSR to initialize
TICK_RATE         = 10000  # Simulator tick rate in milliseconds
```

Edit these values to match your experiment before launching.

### 6.2 — Launching the Full Suite

```bash
cd gardener/
python3 run_benchmarks.py
```

The script will:

1. **Iterate** over each `(radius, horizon)` combination in `COMBINATIONS`
2. For each combination, run `REPETITIONS` independent runs
3. For each run:
   - Clear MongoDB collections (`input_stream`, `output_stream`)
   - Launch the DPSR engine
   - Wait `INITIALIZATION_DELAY` seconds
   - Launch `stream_gardener.py` with the correct parameters
   - Monitor the DPSR log for `step(N)` and `reached` atoms
   - Kill both processes when done
   - Parse the log file with `analyze_dpsr_log.py`
4. **Average** the metrics across all repetitions
5. Save a `summary.txt` report in `log_results/size<N>/`

### 6.3 — Output Structure

```
gardener/
└── log_results/
    └── size200/
        ├── size200_horizon4_radius3_run1.log
        ├── size200_horizon4_radius3_run2.log
        ├── ...
        ├── size200_horizon8_radius5_run10.log
        └── summary.txt          ← averaged metrics per configuration
```

### 6.4 — Live Progress

While running, the script prints a live counter:

```
================================================================================
CONFIG: R=3, H=4
================================================================================

>>> Running: Size=200, Radius=3, Horizon=4, Run=1
>>> Log: log_results/size200/size200_horizon4_radius3_run1.log
[*] Clearing MongoDB...
[*] Waiting 20s for initialization...
[*] Starting Generator: python3 stream_gardener.py ...
  [DPSR] Step: 47/400
```

---

## 7. Analyzing Results

After a run, you can analyze any log file manually:

```bash
python3 analyze_dpsr_log.py log_results/size200/size200_horizon6_radius3_run1.log
```

The script extracts and reports:
- **Average latency** per reasoning step
- **Min / Max latency**
- **Number of steps completed**
- **Norm violation counts** (mud penalty, fire penalty)
- **Goal reached** flag

---

## 8. Saving & Replaying Simulations

Since each new simulation run **clears MongoDB**, it is important to export the data immediately after a run you want to preserve.

### 8.1 — Exporting a Simulation

```bash
python3 export_sim.py log_results/size200/my_run.log
```

This reads the log, queries MongoDB for walls/plants/frogs positions, and saves everything to a self-contained JSON file inside `saved_simulations/`.

### 8.2 — Replaying a Simulation

```bash
python3 replay_interface.py log_results/size200/my_run.log
```

The replay interface **automatically detects** whether a saved JSON exists and loads from there; otherwise it falls back to a live MongoDB query.

### 8.3 — Replay Controls

| Control | Action |
|---|---|
| ▶ **PLAY** (green) | Start smooth playback at 20 FPS |
| ⏹ **STOP** (red) | Pause playback |
| `<<` | Jump to the first step |
| `>>` | Jump to the last step |
| **Slider** | Scrub manually through any step |
| **Scrollbars** | Pan the map (useful for large grids) |

> The replay system uses **pre-caching** and **hybrid drawing** (grid as lines rather than individual rectangles) to remain smooth even on 150×150+ grids.

---

## 9. MongoDB Schema Reference

### `input_stream` — State Updates (Simulator → Reasoner)

**First tick** (includes static elements):

```json
{
  "timestamp": 1234567890.123,
  "type": "state_update",
  "player":  [col, row],
  "target":  [col, row],
  "walls":   [[c1, r1], [c2, r2], "..."],
  "frogs":   [[c1, r1], [c2, r2], "..."],
  "plants":  [[c1, r1], [c2, r2], "..."],
  "horizon": 5,
  "radius":  6,
  "multi":   1
}
```

**Subsequent ticks** (dynamic data only):

```json
{
  "timestamp": 1234567891.123,
  "type": "state_update",
  "frogs":   [[c1, r1], "..."],
  "plants":  [[c1, r1], "..."],
  "horizon": 5,
  "radius":  6,
  "multi":   1
}
```

### `output_stream` — Actions (Reasoner → Simulator)

```json
{
  "timestamp": 1234567891.500,
  "action": 3,
  "source": "reasoner"
}
```

**Action mapping:**

| Value | Direction | Effect |
|---|---|---|
| `0` | Up | `row + 1` |
| `1` | Down | `row - 1` |
| `2` | Left | `col - 1` |
| `3` | Right | `col + 1` |

---

## 10. Changing Grid Size — Policy File Alignment

The DPSR engine uses a Python helper script to look up Q-values from a pre-trained policy. The policy JSON filename is **hardcoded** inside the script and must match the instance you are benchmarking.

**File to edit:**

```
DPSR/queries/external/load_policy.py
```

Open the file and locate the `generate_nearby_actions` function. Near the top of that function you will find a line like:

```python
# Inside generate_nearby_actions()
json_filename = "big-nd-200-001.json"   # ← change this
```

Change the value to match the `.json` policy file you generated in §4. For example:

| Grid size | Instance file | Policy JSON to set |
|---|---|---|
| 30 × 30 | `instances/small-nd-30-001.lp` | `small-nd-30-001.json` |
| 50 × 50 | `instances/small-nd-50-001.lp` | `small-nd-50-001.json` |
| 200 × 200 | `instances/big-nd-200-001.lp` | `big-nd-200-001.json` |

> ⚠️ **If this line is not updated the reasoner will load the wrong Q-table**, causing the agent to make suboptimal or random-looking decisions despite the DPSR engine appearing to work correctly.

The JSON files are resolved relative to the script's own directory (`DPSR/queries/external/`). Make sure you have copied or symlinked the exported `.json` file there (or adjusted the path accordingly).

---

## 11. Creating New Instances

The instance files (`instances/*.lp`) define the environment grid: walls, frogs, plants, player start position, and target. These instances were originally generated by the **emergency-planning** project, which is the baseline system we compare against.

> 📦 **Reference repository:** [https://github.com/S3basuchian/emergency-planning](https://github.com/S3basuchian/emergency-planning)

To create new instances:

1. Clone the emergency-planning repository and follow its own documentation to generate `.lp` map files at the desired grid size.
2. Place the generated `.lp` file inside `gardener/instances/`.
3. Train (or obtain) a Q-table policy for the new instance and export it to JSON using `export_policy.py` (see §4).
4. Update `load_policy.py` to point to the new JSON filename (see §10).
5. Update `INSTANCE_PATH` and `GRID_SIZE` in `run_benchmarks.py` to match the new instance.

---

## 12. Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| `pymongo.errors.OperationFailure: not master` | MongoDB not in ReplicaSet mode | Follow §3 to set up `rs0` |
| DPSR engine exits immediately | Wrong `--program` or `--mongodb-config` path | Verify paths relative to the `DPSR/` directory |
| Simulator sees no output from DPSR | Started simulator before DPSR was ready | Increase `INITIALIZATION_DELAY` in `run_benchmarks.py` |
| `TK Error loading images` in replay | `interface.py` not found | Ensure `interface.py` is in the same `gardener/` directory |
| `Instance file not found` | Wrong path to `.lp` file | Use path relative to `gardener/`, e.g. `instances/big-nd-200-001.lp` |
| MongoDB collections not cleared | `MongoUtils` connection failed | Check that MongoDB is running: `sudo systemctl status mongod` |
| Agent ignores water / norm misbehaves *(new-penalties variant)* | `.water.json` missing or outdated | Re-run `python3 precompute_water.py instances/<name>.lp` (see §4b) |
| Terrain is always the same after re-running *(new-penalties variant)* | `precompute_water.py` was not re-run | The terrain is fixed by the instance file; call `precompute_water.py` again to randomize |

---

*For any issues with the ASP program logic, refer to `program.lp` and `program_global.lp`. For policy format details, see `policy_reader.py`.*
