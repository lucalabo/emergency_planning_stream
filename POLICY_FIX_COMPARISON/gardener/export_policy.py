import pickle
import json
import numpy as np
import os
import sys
from learning import Learning
from instance import read_from_file

def export_policy(instance_name):
    pkl_path = f'instances/learning/{instance_name}.pkl'
    if not os.path.exists(pkl_path):
        print(f"File not found: {pkl_path}")
        return

    print(f"Loading {pkl_path}...")
    try:
        with open(pkl_path, 'rb') as f:
            learning = pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle: {e}")
        return

    # Convert numpy arrays to lists for JSON serialization
    q_table = learning.q_table.tolist() if isinstance(learning.q_table, np.ndarray) else learning.q_table
    
    data = {
        "q_table": q_table,
        "states": learning.states,
        "actions": learning.actions,
        "gamma": learning.gamma,
        "alpha": learning.alpha,
        "epsilon": learning.epsilon
    }

    json_path = f'instances/learning/{instance_name}.json'
    print(f"Exporting to {json_path}...")
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_policy.py <instance_name>")
        # Optional: export all if no arg?
        # For now, let's just list available pickles
        print("Available pickles:")
        if os.path.exists('instances/learning'):
            for f in os.listdir('instances/learning'):
                if f.endswith('.pkl'):
                    print(f" - {f[:-4]}")
    else:
        export_policy(sys.argv[1])
