import os
import time
import random
from datetime import datetime, timedelta
from utils import get_current_time_ms
from mongo_utils import MongoUtils

import signal
import sys
class StreamGame:
    def __init__(self, instance, show=False, tick_rate_ms=1000, horizon=5, radius=6, multi=1, size=30):
        self.instance = instance
        self.show = False
        self.tick_rate_ms = tick_rate_ms
        self.horizon = horizon
        self.radius = radius
        self.multi = multi
        self.mongo = MongoUtils()
        self.last_env_update = 0
        self.last_action_ts = None
        self.first_update_sent = False
        self.running = True
        self.size = size
        self.sim_time = datetime.now()


        
        
        if show:
            from interface import Interface
            self.interface = Interface(instance=instance)
            # Override close event to stop the loop
            self.interface.frame.protocol("WM_DELETE_WINDOW", self.on_close)
        self.register_cleanup_handlers()
    def register_cleanup_handlers(self):
        """Catch termination signals and restore DPSR file properly."""
        def handle_exit(signum, frame):
            print(f"\n[StreamGame] Caught signal {signum}. Cleaning up...")
            try:
                self._restore_dpsr()
            except Exception as e:
                print(f"[StreamGame] Error during cleanup: {e}")
            sys.exit(0)
        # Intercetta segnali comuni di terminazione/process kill
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, handle_exit)
            except Exception:
                pass


    def on_close(self):
        self.running = False
        if self.show:
            self.interface.frame.destroy()

    def update_environment(self,cont_t):
        # Move frogs and other random events
        self.instance.emulate_frogs()
        self.instance.check_violations()
        
        # Stream state to MongoDB
        # We send the current state of the world
        
        # Calculate max_frogs based on radius
        max_frogs = len(self.instance.frogs)
        
        # Get multi from visited count (like in logic.py)
        # This is how many times the player has visited the current position
        multi_value = self.instance.visited.get(self.instance.player, 1)
        
        # Generate new_horizon list (1 to horizon-1) as strings with key "H"
        new_horizon_list = [{"H": str(i)} for i in range(1, self.horizon)]
        
        # Generate generated_frogs list (0 to max_frogs-1) as strings with key "F"
        generated_frogs_list = [{"F": str(i)} for i in range(max_frogs)]
        
        # Generate generated_radius list (-radius to radius) as strings with key "R"
        generated_radius_list = [{"R": str(i)} for i in range(-self.radius, self.radius + 1)]
        
        # Generate fcol and frow for frogs
        fcol_list = []
        frow_list = []
        for f_idx, frog_pos in enumerate(self.instance.frogs):
            if f_idx < max_frogs:  # Only include frogs up to max_frogs
                fcol_list.append({"F": str(f_idx), "C": str(frog_pos[0]), "H": str(0)})
                frow_list.append({"F": str(f_idx), "R": str(frog_pos[1]), "H": str(0)})
        
        # plant and wall are also static facts in the .dpsr file,
        # but we still send them via MongoDB stream as well.
        state_data = {
            "type": "state_update",
            "fcol": fcol_list,
            "frow": frow_list,
            "plant": [{"C": str(p[0]), "R": str(p[1])} for p in self.instance.plants],
            "wall": [{"C": str(w[0]), "R": str(w[1])} for w in self.instance.walls],
            "horizon": [{"H": str(self.horizon)}],
            "radius": [{"R": str(self.radius)}],
            "multi": [{"M": str(multi_value)}],  # Dynamic value from visited
            "size": [{"S": str(self.size)}],
            "num_frogs": [{"F": str(max_frogs)}],
            "num_plants": [{"P": str(len(self.instance.plants))}],
            "new_horizon": new_horizon_list,
            "generated_frogs": generated_frogs_list,
            "generated_radius": generated_radius_list,
        }

        state_data["start_position_player"] = [{"C": str(self.instance.player[0]), "R": str(self.instance.player[1]), "T": str(cont_t)}]
        state_data["target"] = [{"C": str(self.instance.target[0]), "R": str(self.instance.target[1])}]
        state_data["step"] = [{"S": str(cont_t)}]

            
            
        # Generate timestamp in datetime format with milliseconds
        timestamp = self.sim_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-7]  # Remove last 3 digits to get milliseconds
        #self.sim_time += timedelta(milliseconds=self.tick_rate_ms)
        self.sim_time += timedelta(milliseconds=1000)

        timestamp_numerico=str(int(self.sim_time.timestamp()))
        # Use datetime string as timestamp for the state
        print(f"DEBUG: Sending state update for step {cont_t} at {timestamp}")
        self.mongo.write_state(timestamp, state_data)

    def check_actions(self):
        # Poll for new actions from the reasoning system
        # We only care about actions newer than the last one we executed
        action_doc = self.mongo.poll_latest_result(last_timestamp=self.last_action_ts, timeout=0)
        
        if action_doc:
            self.last_action_ts = action_doc.get('timestamp')
            if 'action' in action_doc:
                action = action_doc['action']
                print(f"Executing action: {action}")
                self.instance.execute(action)
                self.instance.check_violations()

    def loop(self, cont_t):
        while self.running:
            current_time = get_current_time_ms()

            # Update environment at fixed rate
            if current_time - self.last_env_update > self.tick_rate_ms:
                cont_t+=1
                self.update_environment(cont_t)
                self.last_env_update = current_time

            # Check for actions continuously (or could be throttled too)
            self.check_actions()

            # Update UI
            if self.show:
                self.interface.place_piece("player", self.instance.player)
                if len(self.instance.frogs) > 0:
                    self.interface.remove_pieces("frog")
                    for c, f in enumerate(self.instance.frogs):
                        self.interface.add_piece("frog_" + str(c),
                                                 self.interface.frog_image, f)
                
                # Schedule next loop - use after for Tkinter event loop compatibility
                self.interface.after(50, lambda: self.loop(cont_t))
                return # Exit this call, let mainloop handle next
            else:
                # If no UI, just sleep a bit and continue loop
                time.sleep(0.05)
                # Continue loop iteratively

    # -----------------------------------------------------------------------
    # Static facts injection into .dpsr
    # -----------------------------------------------------------------------

    def _get_dpsr_path(self):
        """Returns the absolute path of the policy_fix.dpsr file."""
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "..", "DPSR", "queries", "program", "policy_fix.dpsr")

    def _build_static_facts(self):
        """Builds the ASP fact block for plant and wall (static, never change)."""
        lines = [
            "%%%% Static facts injected by stream_game.py (plant, wall) %%%%",
        ]
        for p in self.instance.plants:
            lines.append(f"plant({p[0]},{p[1]}).")
        for w in self.instance.walls:
            lines.append(f"wall({w[0]},{w[1]}).")
        lines.append("%%%% End of static facts %%%%")
        lines.append("")
        return "\n".join(lines) + "\n"

    def _prepend_static_facts_to_dpsr(self):
        """Prepends static plant/wall facts to the .dpsr file.
        Saves the original content so it can be restored later."""
        dpsr_path = self._get_dpsr_path()
        with open(dpsr_path, "r") as f:
            self._dpsr_original_content = f.read()
        static_block = self._build_static_facts()
        with open(dpsr_path, "w") as f:
            f.write(static_block)
            f.write(self._dpsr_original_content)
        print(f"[StreamGame] Static facts (plant/wall) prepended to {dpsr_path}")

    def _restore_dpsr(self):
        """Restores the .dpsr file to its original content."""
        dpsr_path = self._get_dpsr_path()
        if hasattr(self, "_dpsr_original_content"):
            with open(dpsr_path, "w") as f:
                f.write(self._dpsr_original_content)
            print(f"[StreamGame] Restored original .dpsr at {dpsr_path}")

    # -----------------------------------------------------------------------

    def run(self, cont_t=0):
        # Inject static facts (plant, wall) into the .dpsr file
        self._prepend_static_facts_to_dpsr()
        # Wait for DPSR to load the updated program before starting the stream
        print("[StreamGame] Waiting 20 seconds for DPSR to load the updated .dpsr program...")
        time.sleep(20)
        print("[StreamGame] Starting stream...")
        try:
            self.mongo.clear_collections()
            # Initial state send
            self.update_environment(cont_t)
            self.last_env_update = get_current_time_ms()
            if self.show:
                self.loop(cont_t)
                self.interface.mainloop()
            else:
                while self.running:
                    self.loop(cont_t)
        finally:
            # Always restore the original .dpsr file
            self._restore_dpsr()
