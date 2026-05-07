import time
from datetime import datetime, timedelta
from utils import get_current_time_ms
from mongo_utils import MongoUtils

class Logic:
    def __init__(self, instance, learning, horizon, radius):
        self.instance = instance
        self.learning = learning
        self.radius = radius
        self.horizon = horizon
        self.time_diff = []
        self.cache = []
        self.mongo = MongoUtils()
        self.mongo.clear_collections()
        self.sim_time = datetime.now()
        self.last_timestamp = None  # keep track of last processed result timestamp

    def prepare_state_data(self):
        state_data = {
            "multi": [],
            "foutside": [],
            "fcol": [],
            "frow": [],
            "wall": [],
            "plant": [],
            "target": [],
            "action": [],
            "pcol":[],
            "prow":[],
            "horizon":[],
            "radius":[],
            "frogs":[],
            "new_horizon":[],
            "generated_frogs":[],
            "generated_radius":[]
        }

        midpoint = self.instance.player

        multi = self.instance.visited[midpoint]
        print("MULTI:",multi)
        max_frogs = min(pow((self.radius * 2 + 1), 2) - 1,len(self.instance.frogs))
        state_data["multi"].append({"M": str(multi)})
        state_data["horizon"].append({"H": str(self.horizon)})
        state_data["radius"].append({"R": str(self.radius)})
        state_data["frogs"].append({"F": str(max_frogs)})
        state_data["pcol"].append({"C": str(0),"T": str(0)})
        state_data["prow"].append({"R": str(0),"T": str(0)})

        for i in range(1,self.horizon):
            state_data["new_horizon"].append({"H": str(i)})
        for i in range(max_frogs):
            state_data["generated_frogs"].append({"F": str(i)})
        start_radius = self.radius*-1
        for i in range(start_radius,self.radius+1):
            state_data["generated_radius"].append({"R": str(i)})

        # walls & plants
        for i in range(self.radius + 1):
            for j in range(self.radius + 1):
                absolut = (midpoint[0] + i, midpoint[1] + j)
                for a in range(4):
                    r = self.learning.get_action_rank((absolut[0], absolut[1]),
                                                      a)
                    state_data["action"].append({"A": str(a),"S": str(r),"C": str(i),"R": str(j)})
                if absolut == self.instance.target:
                    state_data["target"].append({"C": str(i),"R": str(j)})
                if absolut in self.instance.plants and absolut not in self.instance.dead_plants:
                    state_data["plant"].append({"C": str(i),"R": str(j)})
                if absolut in self.instance.walls:
                    state_data["wall"].append({"C": str(i),"R": str(j)})
                if absolut[0] < 1 or absolut[1] < 1 or absolut[
                    0] > self.instance.size or absolut[
                    1] > self.instance.size:
                    state_data["wall"].append({"C": str(i),"R": str(j)})

                absolut = (midpoint[0] - i, midpoint[1] + j)
                for a in range(4):
                    r = self.learning.get_action_rank((absolut[0], absolut[1]),a)
                    state_data["action"].append({"A": str(a),"S": str(r),"C": str(-i),"R": str(j)})
                if absolut == self.instance.target:
                    state_data["target"].append({"C": str(-i),"R": str(j)})
                if absolut in self.instance.plants and absolut not in self.instance.dead_plants:
                    state_data["plant"].append({"C": str(-i),"R": str(j)})
                if absolut in self.instance.walls:
                    state_data["wall"].append({"C": str(-i),"R": str(j)})
                if absolut[0] < 1 or absolut[1] < 1 or absolut[
                    0] > self.instance.size or absolut[
                    1] > self.instance.size:
                    state_data["wall"].append({"C": str(-i),"R": str(j)})

                absolut = (midpoint[0] + i, midpoint[1] - j)
                for a in range(4):
                    r = self.learning.get_action_rank((absolut[0], absolut[1]),a)
                    state_data["action"].append({"A": str(a),"S": str(r),"C": str(i),"R": str(-j)})
                if absolut == self.instance.target:
                    state_data["target"].append({"C": str(i),"R": str(-j)})
                if absolut in self.instance.plants and absolut not in self.instance.dead_plants:
                    state_data["plant"].append({"C": str(i),"R": str(-j)})
                if absolut in self.instance.walls:
                    state_data["wall"].append({"C": str(i),"R": str(-j)})
                if absolut[0] < 1 or absolut[1] < 1 or absolut[
                    0] > self.instance.size or absolut[
                    1] > self.instance.size:
                    state_data["wall"].append({"C": str(i),"R": str(-j)})

                absolut = (midpoint[0] - i, midpoint[1] - j)
                for a in range(4):
                    r = self.learning.get_action_rank((absolut[0], absolut[1]),a)
                    state_data["action"].append({"A": str(a),"S": str(r),"C": str(-i),"R": str(-j)})
                if absolut == self.instance.target:
                    state_data["target"].append({"C": str(-i),"R": str(-j)})
                if absolut in self.instance.plants and absolut not in self.instance.dead_plants:
                    state_data["plant"].append({"C": str(-i),"R": str(-j)})
                if absolut in self.instance.walls:
                    state_data["wall"].append({"C": str(-i),"R": str(-j)})
                if absolut[0] < 1 or absolut[1] < 1 or absolut[
                    0] > self.instance.size or absolut[
                    1] > self.instance.size:
                    state_data["wall"].append({"C": str(-i),"R": str(-j)})
                if absolut in self.instance.plants and absolut not in self.instance.dead_plants:
                    state_data["plant"].append({"C": str(-i),"R": str(-j)})
                if absolut in self.instance.walls:
                    state_data["wall"].append({"C": str(-i),"R": str(-j)})
                if absolut[0] < 1 or absolut[1] < 1 or absolut[
                    0] > self.instance.size or absolut[
                    1] > self.instance.size:
                    state_data["wall"].append({"C": str(-i),"R": str(-j)})


        # frogs
        count_frog = 0
        for c, f in enumerate(self.instance.frogs):
            relative = (f[0] - midpoint[0], f[1] - midpoint[1])
            if abs(relative[0]) > self.radius or abs(
                    relative[
                        1]) > self.radius or f in self.instance.dead_frogs:
                #    self.ctl.assign_external(Function("foutside", [Number(c)]),
                #                             True)
                pass
            else:
                state_data["fcol"].append({"F": str(count_frog),"C": str(relative[0]),"H": str(0)})
                state_data["frow"].append({"F": str(count_frog),"R": str(relative[1]),"H": str(0)})
                #self.ctl.assign_external(
                #    Function("fcol",
                #             [Number(count_frog), Number(relative[0]),
                #              Number(0)]),
                #    True)
                #self.ctl.assign_external(
                #    Function("frow",
                #             [Number(count_frog), Number(relative[1]),
                #              Number(0)]),
                #    True)
                count_frog += 1
        for i in range(count_frog, max_frogs):
            state_data["foutside"].append({"F": str(i)})


        return state_data

    def get_action(self, cache):
        time_pre_compute = get_current_time_ms()

        # Failsafe: If the framework is stuck in a loop, follow the RL
        if self.instance.visited[self.instance.player] > 10:
            self.cache.clear()
            return self.learning.get_action(self.instance)

        # If there are any cached actions use them first
        if len(self.cache) > 0:
            action = self.cache.pop(0)
            time_post_compute = get_current_time_ms()
            time_diff = time_post_compute - time_pre_compute
            self.time_diff.append(time_diff)
            return action

        self.player = []

        # Prepare state data
        state_data = self.prepare_state_data()
        
        # Generate timestamp for state
        timestamp = self.sim_time.strftime("%Y-%m-%dT%H:%M:%S")
        self.sim_time += timedelta(seconds=1)
        
        print(f"[Logic] Sending state to MongoDB. Timestamp: {timestamp}")
        
        # Write to MongoDB
        self.mongo.write_state(timestamp, state_data)
        
        print(f"[Logic] Waiting for result... (Timestamp: {timestamp})")
        
        # Wait for the latest result (any new document after previous timestamp)
        result = self.mongo.poll_latest_result(self.last_timestamp, timeout=None)
        
        if result is None:
            print(f"[Logic] No result received after timestamp {self.last_timestamp}")
            return None
        
        # Update last_timestamp with the timestamp of the fetched result
        self.last_timestamp = result.get("timestamp")
        
        # Process result
        # The result may contain an 'answers' field with a string representation of action_taken entries.
        # Example: result["answers"] = ["[action_taken(0,1,1,0), action_taken(3,0,0,0)]"]
        # We need to parse this into the same structure expected downstream (a list of dicts with keys "0","1","2","3").
        import re
        action = result.get("action")
        # If the result contains the new 'answers' format, parse it.
        if result and "answers" in result and isinstance(result["answers"], list) and len(result["answers"]) > 0:
            answers_str = result["answers"][0]
            # Find all action_taken(...) occurrences
            matches = re.findall(r"action_taken\((\d+),(\d+),(\d+),(\d+)\)", answers_str)
            parsed_actions = []
            for act, tim, col, row in matches:
                parsed_actions.append({"0": act, "1": tim, "2": col, "3": row})
            # Replace or add to result for downstream processing
            result["action_taken"] = parsed_actions

        print(f"[Logic] Result received! (Timestamp: {self.last_timestamp})")
        
        if result:
            
            if "action_taken" in result:
                max_time = 0
                actions_map = {}
                
                for item in result["action_taken"]:
                    action_val = int(item.get("0", 0))
                    time_step = int(item.get("1", 0))
                    
                    if time_step > max_time:
                        max_time = time_step
                    actions_map[time_step] = action_val
                
                self.player = [0] * (max_time + 1)
                for t, a in actions_map.items():
                    self.player[t] = a
            else:
                print(f"[Logic] Warning: No action_taken found in result for {timestamp}")
                pass
        else:
            # This should technically not be reached with infinite timeout unless interrupted
            print("[Logic] Error: Poll returned None (unexpected).")
            return self.learning.get_action(self.instance)

        # measure the computation time
        time_post_compute = get_current_time_ms()
        time_diff = time_post_compute - time_pre_compute
        self.time_diff.append(time_diff)

        # cache further actions if desired and return current next action
        if not self.player:
             return self.learning.get_action(self.instance)

        action = self.player[0]
        if cache > 1:
            for i in range(1, cache):
                if i < len(self.player):
                    rel = self.player[i]
                    self.cache.append(rel)
        return action

    def setup(self):
        # No longer needed for Clingo, but kept for compatibility if called
        pass
