import json
import os
import sys

#action 0 -> down
#action 1 -> up
#action 2 -> left
#action 3 -> right

def load_policy(json_filename):
    """
    Carica il file JSON dalla stessa cartella dello script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, json_filename)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data


def get_action_rank_from_q_values(q_values, action):
    """
    Restituisce il rank dell'azione (0=peggiore, 3=migliore) basato sui Q-values.
    """
    # Crea lista di (azione, valore)
    action_values = []
    for i, val in enumerate(q_values):
        action_values.append((i, val))
    
    # Ordina per valore crescente (come np.argsort)
    action_values.sort(key=lambda x: x[1])
    
    # Trova l'indice dell'azione richiesta
    for rank, (act, val) in enumerate(action_values):
        if act == action:
            return rank
    return -1

def generate_nearby_actions(player_col, player_row, radius):
    """
    Genera i fatti 'action' per tutte le celle nel raggio specificato attorno al giocatore.
    Usa coordinate ASSOLUTE invece di relative.
    Replica la logica di logic.py ma con posizioni assolute.
    
    Args:
        player_col: colonna della posizione del player
        player_row: riga della posizione del player
        radius: raggio di celle da considerare attorno al player
    
    Returns:
        Tuple di liste, dove ogni lista rappresenta un'azione: [A, S, C, R]
        Esempio: list1, list2, list3, ... = generate_nearby_actions(...)
        dove list1 = [azione, rank, col, row]
    """
    json_filename="big-nd-150-001.json"
    policy_data = load_policy(json_filename)
        
    actions_lists = []  # Lista temporanea per raccogliere tutte le liste
    midpoint = (player_col, player_row)
    processed_cells = set()  # Track processed cells to avoid duplicates
    
    # Helper per processare una cella
    def process_cell(abs_col, abs_row):
        # Skip if already processed
        if (abs_col, abs_row) in processed_cells:
            return
        processed_cells.add((abs_col, abs_row))
        
        target_state = [abs_col, abs_row]
        try:
            state_idx = policy_data['states'].index(target_state)
            q_values = policy_data['q_table'][state_idx]
            
            for a in range(4):
                r = get_action_rank_from_q_values(q_values, a)
                # Crea una lista separata per ogni azione
                action_list = [a, r, abs_col, abs_row]
                actions_lists.append(action_list)
        except ValueError:
            # Stato non trovato (es. muro o fuori mappa)
            pass

    # Logica dei 4 quadranti come in logic.py
    for i in range(radius + 1):
        for j in range(radius + 1):
            # Quadrante 1 (+i, +j)
            process_cell(midpoint[0] + i, midpoint[1] + j)
            
            # Quadrante 2 (-i, +j)
            process_cell(midpoint[0] - i, midpoint[1] + j)
            
            # Quadrante 3 (+i, -j)
            process_cell(midpoint[0] + i, midpoint[1] - j)
            
            # Quadrante 4 (-i, -j)
            process_cell(midpoint[0] - i, midpoint[1] - j)
    
    # Restituisci come tuple di liste separate
    return tuple(actions_lists)


def generate_water_actions(player_col, player_row, radius):
    """
    Genera i fatti 'water_action' per tutte le celle nel raggio specificato attorno al giocatore.
    Usa policy specifica per l'acqua (current_water_policy.json).
    """
    json_filename = "big-nd-150-001.water.json"
    
    # Check if policy exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(script_dir, json_filename)):
        # Silent fail or return nothing
        return tuple()
        
    policy_data = load_policy(json_filename)
        
    actions_lists = []  # Lista temporanea per raccogliere tutte le liste
    midpoint = (player_col, player_row)
    processed_cells = set()  # Track processed cells to avoid duplicates
    
    # Helper per processare una cella
    def process_cell(abs_col, abs_row):
        # Skip if already processed
        if (abs_col, abs_row) in processed_cells:
            return
        processed_cells.add((abs_col, abs_row))
        
        target_state = [abs_col, abs_row]
        try:
            state_idx = policy_data['states'].index(target_state)
            q_values = policy_data['q_table'][state_idx]
            
            for a in range(4):
                r = get_action_rank_from_q_values(q_values, a)
                # Crea una lista separata per ogni azione: [A, Rank, C, R]
                action_list = [a, r, abs_col, abs_row]
                actions_lists.append(action_list)
        except ValueError:
            # Stato non trovato (es. muro o fuori mappa)
            pass

    # Logica dei 4 quadranti come in logic.py
    for i in range(radius + 1):
        for j in range(radius + 1):
            process_cell(midpoint[0] + i, midpoint[1] + j)
            process_cell(midpoint[0] - i, midpoint[1] + j)
            process_cell(midpoint[0] + i, midpoint[1] - j)
            process_cell(midpoint[0] - i, midpoint[1] - j)
    
    return tuple(actions_lists)

