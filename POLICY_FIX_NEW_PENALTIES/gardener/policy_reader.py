import json
import os
import sys

def load_policy(json_filename):
    """
    Carica il file JSON dalla stessa cartella dello script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, json_filename)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def get_action_from_policy(policy_data, player_pos):
    """
    Calcola la migliore azione dato la posizione del giocatore (col, row).
    Restituisce un dizionario con:
    - 'best_action': l'azione con il rank maggiore
    - 'all_actions': lista di tuple (action, rank) ordinate per rank decrescente
    - 'q_values': dizionario {action: rank} per tutte le azioni
    """
    target_state = list(player_pos)  # convert tuple to list
    
    try:
        state_idx = policy_data['states'].index(target_state)
    except ValueError:
        print(f"State {target_state} not found in policy states.")
        return None

    q_values = policy_data['q_table'][state_idx]

    # Trova l'indice del massimo senza numpy
    best_action_idx = max(range(len(q_values)), key=lambda i: q_values[i])
    best_action = policy_data['actions'][best_action_idx]
    
    # Crea una lista di tuple (action, rank) per tutte le azioni
    all_actions_with_ranks = [
        (policy_data['actions'][i], q_values[i]) 
        for i in range(len(q_values))
    ]
    
    # Ordina per rank decrescente
    all_actions_with_ranks.sort(key=lambda x: x[1], reverse=True)
    
    # Crea un dizionario action -> rank
    q_values_dict = {
        policy_data['actions'][i]: q_values[i] 
        for i in range(len(q_values))
    }
    
    return {
        'best_action': best_action,
        'all_actions': all_actions_with_ranks,
        'q_values': q_values_dict
    }

def retrieve_action(col, row, action_rank=3):
    """
    Recupera un'azione dalla policy in base alla posizione e al ranking desiderato.
    
    Args:
        col: colonna della posizione del giocatore
        row: riga della posizione del giocatore
        action_rank: quale azione scegliere (0-3)
                     3 = migliore (default)
                     2 = seconda migliore
                     1 = terza migliore
                     0 = peggiore
    
    Returns:
        tuple: (action, col, row) dove action è l'azione selezionata
    """
    json_filename = "instances/learning/small-nd-30-001.json"
    print(f"Loading policy from {json_filename}...")
    policy = load_policy(json_filename)
    
    result = get_action_from_policy(policy, (col, row))
    
    if result is None:
        return None, col, row
    
    action_names = {0: "RIGHT", 1: "LEFT", 2: "UP", 3: "DOWN"}
    
    # Converti action_rank (3=best, 0=worst) in indice della lista (0=best, 3=worst)
    index = 3 - action_rank
    
    # Verifica che l'indice sia valido
    if index < 0 or index >= len(result['all_actions']):
        print(f"Warning: action_rank {action_rank} non valido. Usando la migliore azione.")
        index = 0
    
    # Seleziona l'azione in base all'indice
    selected_action, selected_rank = result['all_actions'][index]
    
    print(f"Player Position: ({col}, {row})")
    print(f"Action rank requested: {action_rank} (0=worst, 3=best)")
    print(f"Selected Action: {selected_action} ({action_names.get(selected_action, 'Unknown')}) with Q-value: {selected_rank}")
    print("\nAll actions ranked by Q-value:")
    for i, (action, rank) in enumerate(result['all_actions']):
        marker = " ← SELECTED" if action == selected_action and rank == selected_rank else ""
        print(f"  [{3-i}] {action} ({action_names.get(action, 'Unknown')}): {rank}{marker}")
    
    return selected_action, col, row


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

def generate_nearby_actions(player_col, player_row, radius, policy_data=None, json_filename="instances/learning/small-nd-30-001.json"):
    """
    Genera i fatti 'action' per tutte le celle nel raggio specificato attorno al giocatore.
    Usa coordinate ASSOLUTE invece di relative.
    Replica la logica di logic.py ma con posizioni assolute.
    
    Args:
        player_col: colonna della posizione del player
        player_row: riga della posizione del player
        radius: raggio di celle da considerare attorno al player
        policy_data: dati della policy (opzionale, verrà caricato se None)
        json_filename: percorso del file JSON della policy
    
    Returns:
        Tuple di liste, dove ogni lista rappresenta un'azione: [A, S, C, R]
        Esempio: list1, list2, list3, ... = generate_nearby_actions(...)
        dove list1 = [azione, rank, col, row]
    """
    if policy_data is None:
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

if __name__ == "__main__":
    # Test con posizione colonna 8, riga 13
    print("=" * 60)
    print("TEST: Selezionando diverse azioni in base al rank")
    print("=" * 60)
    
    for rank in [3, 2, 1, 0]:
        print(f"\n{'=' * 60}")
        print(f"Richiesta azione con rank {rank}")
        print("=" * 60)
        action, col, row = retrieve_action(8, 13, action_rank=rank)
        print(f"Returned: action={action}, col={col}, row={row}")
    
    print("\n" + "=" * 60)
    print("TEST: Generazione azioni nearby con posizioni assolute (radius=2)")
    print("=" * 60)
    nearby_actions = generate_nearby_actions(8, 13, radius=2)
    print(f"Generated {len(nearby_actions)} action lists.")
    if len(nearby_actions) > 0:
        print("First 5 action lists:")
        for i, action_list in enumerate(nearby_actions[:5]):
            print(f"  Action {i+1}: {action_list} -> [A={action_list[0]}, S={action_list[1]}, C={action_list[2]}, R={action_list[3]}]")





