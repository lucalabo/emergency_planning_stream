
import json
import os
import random
import sys
from collections import deque
import instance

def calculate_water_policy(inst):
    """
    Computes Q-values for reaching the nearest water cell.
    Q(s, a) = -distance(next_s, nearest_water)
    """
    size = inst.size
    walls = set(inst.walls)
    water_cells = set()
    
    if hasattr(inst, 'properties'):
        for loc, props in inst.properties.items():
            if 'water' in props:
                water_cells.add(loc)
    
    # BFS to find shortest distance to water for all cells
    dist_matrix = {}
    queue = deque()
    
    for w in water_cells:
        dist_matrix[w] = 0
        queue.append(w)
        
    visited = set(water_cells)
    
    # Directions: 0:Down(0,1), 1:Up(0,-1), 2:Left(-1,0), 3:Right(1,0)
    # Check instance.py execute method:
    # 0 -> y+1 (Down/South if y increases downwards? Usually standard is 0,0 top-left but check ASP)
    # ASP: p(R+1,C,T+1) :- s(T). s is South. 
    # instance.py: 0 -> y+1. If y is Row, then yes.
    # instance.py: player = (x, y). 
    # execute: 0 -> y+1 (Row+1). 1 -> y-1 (Row-1). 
    # 2 -> x-1 (Col-1). 3 -> x+1 (Col+1).
    # Wait, usually (x,y) -> (col, row).
    # If x is Col, y is Row:
    # 0 (y+1) -> Row+1 (South). Correct.
    # 1 (y-1) -> Row-1 (North). Correct.
    # 2 (x-1) -> Col-1 (West). Correct.
    # 3 (x+1) -> Col-1 (East). Correct.
    
    # Directions for BFS (inverse doesn't matter for undirected graph but let's be consistent)
    # Neighbors of (x, y)
    moves = [(0, 1), (0, -1), (-1, 0), (1, 0)]
    
    while queue:
        curr = queue.popleft()
        cx, cy = curr
        cdist = dist_matrix[curr]
        
        for dx, dy in moves:
            nx, ny = cx + dx, cy + dy
            if 1 <= nx <= size and 1 <= ny <= size and (nx, ny) not in walls:
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    dist_matrix[(nx, ny)] = cdist + 1
                    queue.append((nx, ny))
                    
    # Now build Q-table
    states = []
    q_table = []
    
    # For every cell in the grid
    for r in range(1, size + 1):
        for c in range(1, size + 1):
            # State is [col, row] -> [c, r]?
            # load_policy uses absolute coordinates.
            # In generate_nearby_actions: process_cell(midpoint[0] + i, ...)
            # midpoint is player (col, row). 
            # So states should be [c, r] matches (x, y).
            
            # If cell is a wall, we might still want it in the list if load_policy queries it, 
            # but usually walls are walls. Let's include everything to be safe or just valid cells.
            # load_policy handles missing states gracefully (try/except).
            
            # However, if we are ON a wall (impossible), doesn't matter.
            # But we need q-values for all reachable cells.
            
            if (c, r) in walls:
                continue

            state = [c, r]
            qs = []
            
            # Calculate Q-values for actions 0, 1, 2, 3
            # Action 0: (c, r+1)
            # Action 1: (c, r-1)
            # Action 2: (c-1, r)
            # Action 3: (c+1, r)
            
            actions = [
                (c, r+1), # 0
                (c, r-1), # 1
                (c-1, r), # 2
                (c+1, r)  # 3
            ]
            
            for next_pos in actions:
                nx, ny = next_pos
                if 1 <= nx <= size and 1 <= ny <= size and (nx, ny) not in walls:
                    # Valid move
                    if (nx, ny) in dist_matrix:
                        d = dist_matrix[(nx, ny)]
                        # Q = -distance (closer is better, so less negative is higher)
                        qs.append(-float(d))
                    else:
                        # Reachable but no path to water? (e.g. enclosed area without water)
                        # Penalty
                        qs.append(-9999.0)
                else:
                    # Invalid move (wall or out of bounds)
                    qs.append(-9999.0)
            
            states.append(state)
            q_table.append(qs)
            
    return {"states": states, "q_table": q_table}

def process_instance(filename):
    print(f"Processing {filename}...")
    inst = instance.read_from_file(filename)
    
    # Always regenerate properties for the stream game to have variety
    has_props = False
    
    # Target configurations
    configs = [
        ('water', 0.10),
        ('mud', 0.05),
        ('oil', 0.05),
        ('fire', 0.05)
    ]
    
    total_cells = inst.size * inst.size
    
    # Clear existing properties to regenerate
    if hasattr(inst, 'properties') and inst.properties:
        inst.properties = {}
        
    if not has_props:
        print("Generating new properties...")
        # Generate properties
        # Water 15%, others 10%
        # Exclude walls, start, target, plants, frogs? 
        # instance.py create_random_instance logic:
        # occupied: walls, player, target, plants, frogs.
        
        occupied = set(inst.walls)
        occupied.add(inst.player)
        occupied.add(inst.target)
        for p in inst.plants: occupied.add(p)
        for f in inst.frogs: occupied.add(f)
        
        props_map = {}
        
        # We need to distribute them randomly
        # To avoid overlaps and ensure exact percentages, let's create a list of available cells
        available_cells = []
        for r in range(1, inst.size + 1):
            for c in range(1, inst.size + 1):
                if (c, r) not in occupied:
                    available_cells.append((c, r))
                    
        random.shuffle(available_cells)
        
        idx = 0
        for p_type, pct in configs:
            count = int(total_cells * pct)
            for _ in range(count):
                if idx < len(available_cells):
                    loc = available_cells[idx]
                    if loc not in props_map:
                        props_map[loc] = []
                    props_map[loc].append(p_type)
                    idx += 1
                else:
                    break
                    
        inst.properties = props_map
        inst.save() # Overwrite/Update the instance file with properties
        print("Properties saved to instance file.")
    else:
        print("Properties already exist using them.")
        
    # Generate Water Policy
    print("Generating Water Policy...")
    policy_data = calculate_water_policy(inst)
    
    policy_filename = filename.replace('.lp', '.water.json')
    with open(policy_filename, 'w') as f:
        json.dump(policy_data, f)
    print(f"Water policy saved to {policy_filename}")
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 precompute_water.py <instance_file>")
        sys.exit(1)
        
    filename = sys.argv[1]
    process_instance(filename)
