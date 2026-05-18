#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="$(cd "$(dirname "$0")" && pwd)"
GARDENER_DIR="$(cd "$BENCH_DIR/.." && pwd)"
START_LIST="$BENCH_DIR/start_list.txt"

total=$(wc -l < "$START_LIST")
count=0

while IFS= read -r rel_path; do
    count=$((count + 1))
    start_sh="$BENCH_DIR/$rel_path"
    run_dir="$(dirname "$start_sh")"

    echo "[$count/$total] $rel_path"

    if [ -f "$run_dir/00_finished.log" ]; then
        echo "  Skipping (already finished)"
        continue
    fi

    # Extract gardener args: everything between "python3 gardener.py" and the /dev/shm instance path
    args=$(grep "python3 gardener.py" "$start_sh" | sed 's|.*python3 gardener.py ||; s| /dev/shm.*||')

    # Extract instance filename from the /dev/shm/.../input/<file> path on the run line
    instance_file=$(grep "python3 gardener.py" "$start_sh" | sed 's|.*/input/||; s| 2>.*||; s|[[:space:]]*$||')

    instance_path="$GARDENER_DIR/instances_test/$instance_file"

    if [ ! -f "$instance_path" ]; then
        echo "  ERROR: instance file not found: $instance_path" >&2
        continue
    fi

    cd "$GARDENER_DIR"
    # shellcheck disable=SC2086
    python3 gardener.py $args "$instance_path" \
        > "$run_dir/stdout.log" \
        2> "$run_dir/stderr.log"

    touch "$run_dir/00_finished.log"
    echo "  Done"

done < "$START_LIST"

echo "All runs complete."
