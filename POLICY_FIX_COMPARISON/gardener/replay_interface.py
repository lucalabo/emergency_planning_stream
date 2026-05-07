import tkinter as tk
import re
import os
import sys
import argparse
import json
from pymongo import MongoClient

# Import Image Data from interface.py
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from interface import (
        IMAGEDATA_PLAYER, IMAGEDATA_TARGET, IMAGEDATA_PLANT, 
        IMAGEDATA_FROG
    )
except ImportError:
    IMAGEDATA_PLAYER = IMAGEDATA_TARGET = IMAGEDATA_PLANT = IMAGEDATA_FROG = ""

class ReplayInterface(tk.Frame):
    def __init__(self, target_path, mongo_uri="mongodb://localhost:27017/", db_name="gardener_db"):
        self.target_path = target_path
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        
        self.root = tk.Tk()
        self.root.title("Gardener Replay")
        
        self.cell_size = 24
        self.color1 = "white"
        self.color2 = "grey"
        
        self.states = []
        self.current_index = 0
        self.auto_play = False
        self.pieces = {}
        self.cached_frogs = {} 
        
        # UI Setup
        tk.Frame.__init__(self, self.root)
        self.pack(side="top", fill="both", expand=True)

        try:
            self.player_img = tk.PhotoImage(data=IMAGEDATA_PLAYER)
            self.target_img = tk.PhotoImage(data=IMAGEDATA_TARGET)
            self.plant_img = tk.PhotoImage(data=IMAGEDATA_PLANT)
            self.frog_img = tk.PhotoImage(data=IMAGEDATA_FROG)
        except:
            self.player_img = self.target_img = self.plant_img = self.frog_img = None

        # 1. Load Data (JSON or LOG+DB)
        self.load_simulation_data()
        
        # 3. GUI Layout
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(side="top", fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0, background="bisque")
        self.vbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.hbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        
        self.vbar.pack(side="right", fill="y")
        self.hbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Controls
        controls = tk.Frame(self)
        controls.pack(side="bottom", fill="x", pady=5)
        
        tk.Button(controls, text=" |<< ", command=self.first_step).pack(side="left", padx=2)
        tk.Button(controls, text="  <  ", command=self.prev_step).pack(side="left", padx=2)
        self.play_btn = tk.Button(controls, text=" PLAY ", bg="#2ecc71", fg="white", font=('Arial', 10, 'bold'), command=self.start_play)
        self.play_btn.pack(side="left", padx=10)
        tk.Button(controls, text=" STOP ", bg="#e74c3c", fg="white", font=('Arial', 10, 'bold'), command=self.stop_play).pack(side="left", padx=10)
        tk.Button(controls, text="  >  ", command=self.next_step).pack(side="left", padx=2)
        tk.Button(controls, text=" >>| ", command=self.last_step).pack(side="left", padx=2)
        
        self.status_label = tk.Label(controls, text="Step: 0", font=('Arial', 10, 'bold'))
        self.status_label.pack(side="right", padx=15)
        
        self.slider = tk.Scale(controls, from_=0, to=len(self.states)-1, orient="horizontal", command=self.on_slider_change)
        self.slider.pack(side="bottom", fill="x", padx=10)
        
        self.draw_static_grid()
        self.update_display()

    def load_simulation_data(self):
        # Case A: Input is a saved JSON
        if self.target_path.endswith(".json"):
            self.load_from_json(self.target_path)
            return

        # Case B: Input is a LOG, check for existing JSON in saved_simulations
        run_name = os.path.basename(self.target_path).replace(".log", "")
        saved_path = os.path.join("saved_simulations", f"{run_name}.json")
        if os.path.exists(saved_path):
            print(f"Loading local save found at: {saved_path}")
            self.load_from_json(saved_path)
            return

        # Case C: Fallback to MongoDB
        print("No local save found. Connecting to MongoDB...")
        self.load_from_mongo()

    def load_from_json(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
            self.root.title(f"Persisted Replay: {data['run_name']}")
            self.states = data["states"]
            self.grid_size = data["env"]["size"]
            self.target = tuple(data["env"]["target"])
            self.walls = set(tuple(w) for w in data["env"]["walls"])
            self.plants = set(tuple(p) for p in data["env"]["plants"])
            # Load frogs cache
            for i, frog_list in enumerate(data["frog_cache"]):
                self.cached_frogs[i] = [tuple(f) for f in frog_list]
        print(f"Successfully loaded {len(self.states)} steps from JSON.")

    def load_from_mongo(self):
        # Original logic with pre-caching
        with open(self.target_path, 'r') as f:
            log_data = f.read()
        
        answers = re.findall(r"ANSWER>.*\(datetime\)\s*([\d\-T\:]+).*?\n.*\[(.*?)\]", log_data, re.MULTILINE)
        for ts, content in answers:
            pp = re.search(r"positionPlayer\((\d+),(\d+)\)", content)
            st = re.search(r"step\((\d+)\)", content)
            if pp and st:
                self.states.append({"timestamp": ts, "player": (int(pp.group(1)), int(pp.group(2))), "step": int(st.group(1))})

        client = MongoClient(self.mongo_uri)
        db = client[self.db_name]
        collection = db["input_stream"]
        
        first_doc = collection.find_one({"timestamp": self.states[0]["timestamp"]})
        if not first_doc: first_doc = collection.find_one()
        
        self.grid_size = int(first_doc.get("size", [{"S": "30"}])[0]["S"])
        self.target = (int(first_doc["target"][0]["C"]), int(first_doc["target"][0]["R"]))
        self.walls = set((int(w["C"]), int(w["R"])) for w in first_doc.get("wall", []))
        self.plants = set((int(p["C"]), int(p["R"])) for p in first_doc.get("plant", []))

        all_timestamps = [s["timestamp"] for s in self.states]
        cursor = collection.find({"timestamp": {"$in": all_timestamps}})
        ts_map = {doc["timestamp"]: doc for doc in cursor}
        
        last_doc = None
        for i, state in enumerate(self.states):
            doc = ts_map.get(state["timestamp"])
            if not doc: doc = last_doc
            frogs = []
            if doc and "fcol" in doc and "frow" in doc:
                cols = {item["F"]: int(item["C"]) for item in doc["fcol"] if str(item.get("H")) == "0"}
                rows = {item["F"]: int(item["R"]) for item in doc["frow"] if str(item.get("H")) == "0"}
                for f_id, col in cols.items():
                    if f_id in rows: frogs.append((col, rows[f_id]))
            self.cached_frogs[i] = frogs
            if doc: last_doc = doc

    def draw_static_grid(self):
        self.canvas.delete("all")
        total_px = self.grid_size * self.cell_size
        self.canvas.create_rectangle(0, 0, total_px, total_px, fill=self.color1, outline="")
        for (c, r) in self.walls:
            x1, y1 = (c-1)*self.cell_size, (r-1)*self.cell_size
            self.canvas.create_rectangle(x1, y1, x1+self.cell_size, y1+self.cell_size, fill=self.color2, outline="")
        for i in range(self.grid_size + 1):
            pos = i * self.cell_size
            self.canvas.create_line(pos, 0, pos, total_px, fill="black"); self.canvas.create_line(0, pos, total_px, pos, fill="black")
        self.add_piece("target", self.target_img, self.target, "red")
        for i, plant in enumerate(self.plants): self.add_piece(f"plant_{i}", self.plant_img, plant, "yellow")
        self.canvas.config(scrollregion=(0, 0, total_px, total_px))
        
    def add_piece(self, name, image, pos, color):
        if image: self.canvas.create_image(0, 0, image=image, tags=(name, "piece"), anchor="c")
        else: self.canvas.create_oval(0, 0, 0, 0, fill=color, tags=(name, "piece"))
        self.place_piece(name, pos)

    def place_piece(self, name, pos):
        item = self.canvas.find_withtag(name)
        if not item: return
        if self.canvas.type(item[0]) == "image":
            # Usando pos[0] e pos[1]
            x, y = (pos[0]-1)*self.cell_size + self.cell_size//2, (pos[1]-1)*self.cell_size + self.cell_size//2
            self.canvas.coords(name, x, y)
        else:
            x1, y1 = (pos[0]-1)*self.cell_size, (pos[1]-1)*self.cell_size
            self.canvas.coords(name, x1, y1, x1+self.cell_size, y1+self.cell_size)

    def update_display(self):
        if not self.states: return
        state = self.states[self.current_index]
        self.status_label.config(text=f"Step: {state['step']} | Time: {state['timestamp']}")
        self.slider.set(self.current_index)
        
        # Player (Handle both JSON [list] and Mongo [tuple])
        p_pos = tuple(state["player"])
        if "player" not in self.pieces:
            self.add_piece("player", self.player_img, p_pos, "#3498db")
            self.pieces["player"] = True
        else:
            self.place_piece("player", p_pos)
            
        current_frogs = self.cached_frogs.get(self.current_index, [])
        self.canvas.itemconfigure("frog", state="hidden")
        for i, pos in enumerate(current_frogs):
            fname = f"f_{i}"
            item = self.canvas.find_withtag(fname)
            if not item:
                self.add_piece(fname, self.frog_img, pos, "#2ecc71"); self.canvas.addtag_withtag("frog", fname)
            else:
                self.canvas.itemconfigure(fname, state="normal"); self.place_piece(fname, pos)
        self.canvas.tag_raise("piece")
        px, py = (p_pos[0]-1)*self.cell_size, (p_pos[1]-1)*self.cell_size
        self.canvas.xview_moveto(max(0, (px - 350) / (self.grid_size * self.cell_size)))
        self.canvas.yview_moveto(max(0, (py - 250) / (self.grid_size * self.cell_size)))

    def next_step(self):
        if self.current_index < len(self.states) - 1:
            self.current_index += 1; self.update_display()
        else: self.stop_play()

    def prev_step(self):
        if self.current_index > 0: self.current_index -= 1; self.update_display()

    def first_step(self): self.current_index = 0; self.update_display()
    def last_step(self): self.current_index = len(self.states) - 1; self.update_display()
    def start_play(self): 
        if not self.auto_play: self.auto_play = True; self.run_auto_play()
    def stop_play(self): self.auto_play = False
    def run_auto_play(self):
        if self.auto_play: self.next_step(); self.root.after(50, self.run_auto_play)
    def on_slider_change(self, val):
        ni = int(float(val))
        if ni != self.current_index: self.current_index = ni; self.update_display()
    def run(self): self.root.mainloop()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('file_path', help="Path to .log or .json file")
    p.add_argument('--uri', default="mongodb://localhost:27017/")
    p.add_argument('--db', default="gardener_db")
    args = p.parse_args()
    ReplayInterface(args.file_path, args.uri, args.db).run()
