import re
import os
import json
import argparse
from pymongo import MongoClient

def export_simulation(log_path, mongo_uri, db_name, output_dir="saved_simulations"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    run_name = os.path.basename(log_path).replace(".log", "")
    output_file = os.path.join(output_dir, f"{run_name}.json")
    
    print(f"Exporting data for: {run_name}")
    
    # 1. Parse Log
    states = []
    with open(log_path, 'r') as f:
        log_data = f.read()
    
    answers = re.findall(r"ANSWER>.*\(datetime\)\s*([\d\-T\:]+).*?\n.*\[(.*?)\]", log_data, re.MULTILINE)
    for ts, content in answers:
        pp = re.search(r"positionPlayer\((\d+),(\d+)\)", content)
        st = re.search(r"step\((\d+)\)", content)
        if pp and st:
            # Normalize timestamp: Dpsr might truncate :00 if exactly on the minute
            normalized_ts = ts
            if len(ts) == 16:
                normalized_ts += ":00"
            
            states.append({
                "timestamp": normalized_ts,
                "player": [int(pp.group(1)), int(pp.group(2))],
                "step": int(st.group(1))
            })

            
    if not states:
        print("No ANSWER blocks found in log.")
        return

    # 2. Connect to Mongo
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db["input_stream"]
    
    # 3. Fetch Global Env
    first_ts = states[0]["timestamp"]
    env_doc = collection.find_one({"timestamp": first_ts})
    if not env_doc: env_doc = collection.find_one()
    
    if not env_doc:
        print("No environment data found in MongoDB.")
        return

    # Extract env
    env = {
        "size": int(env_doc.get("size", [{"S": "30"}])[0]["S"]),
        "target": [int(env_doc["target"][0]["C"]), int(env_doc["target"][0]["R"])],
        "walls": [[int(w["C"]), int(w["R"])] for w in env_doc.get("wall", [])],
        "plants": [[int(p["C"]), int(p["R"])] for p in env_doc.get("plant", [])],
        "mud": [[int(p["C"]), int(p["R"])] for p in env_doc.get("mud", [])],
        "water": [[int(p["C"]), int(p["R"])] for p in env_doc.get("water", [])],
        "oil": [[int(p["C"]), int(p["R"])] for p in env_doc.get("oil", [])],
        "fire": [[int(p["C"]), int(p["R"])] for p in env_doc.get("fire", [])],
    }


    # 4. Fetch Frog Cache
    all_ts = [s["timestamp"] for s in states]
    cursor = collection.find({"timestamp": {"$in": all_ts}})
    ts_map = {doc["timestamp"]: doc for doc in cursor}
    
    frog_cache = []
    last_doc = None
    for i, state in enumerate(states):
        doc = ts_map.get(state["timestamp"])
        if not doc: doc = last_doc
        
        frogs = []
        if doc and "fcol" in doc and "frow" in doc:
            cols = {item["F"]: int(item["C"]) for item in doc["fcol"] if str(item.get("H")) == "0"}
            rows = {item["F"]: int(item["R"]) for item in doc["frow"] if str(item.get("H")) == "0"}
            for f_id, col in cols.items():
                if f_id in rows:
                    frogs.append([col, rows[f_id]])
        frog_cache.append(frogs)
        if doc: last_doc = doc

    # 5. Save everything
    package = {
        "run_name": run_name,
        "env": env,
        "states": states,
        "frog_cache": frog_cache
    }
    
    with open(output_file, 'w') as f:
        json.dump(package, f)
        
    print(f"Successfully saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('log_file')
    p.add_argument('--uri', default="mongodb://localhost:27017/")
    p.add_argument('--db', default="gardener_db")
    args = p.parse_args()
    export_simulation(args.log_file, args.uri, args.db)
