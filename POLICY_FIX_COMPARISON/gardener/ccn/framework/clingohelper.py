import clingo
import numpy as np
from clingo import Function, Number


class ClingoHelper:

    def __init__(self, size, horizon, low_prio_age, high_prio_age, prefixes, low_prio, high_prio):
        self.size = size
        self.horizon = horizon
        self.low_prio_age = low_prio_age
        self.low_prio = low_prio
        self.high_prio_age = high_prio_age
        self.high_prio = high_prio
        self.prefixes = prefixes
        self.ctl = None
        self.setup()

    def on_model(self, m):
        self.save_solution(m)
        show = " ".join([str(i) for i in m.symbols(shown=True)])
        #print("Answer:\n{}".format(show))

    def save_solution(self, m):
        self.action = []
        for sym in m.symbols(shown=True):
            match sym.name:
                case "action":
                    if len(sym.arguments) == 2:
                        while len(self.action) < sym.arguments[0].number + 1:
                            self.action.append((0, 0))
                        self.action[sym.arguments[0].number] = (
                            sym.arguments[0].number,
                            sym.arguments[1].number)

    def setup(self):
        self.ctl = clingo.Control(["-c", f"size={self.size}",
                                   "-c", f"prefixes={len(self.prefixes)}",
                                   "-c", f"horizon={self.horizon}",
                                   "-c", f"high_prio_age={self.high_prio_age}",
                                   "-c", f"low_prio_age={self.low_prio_age}"])
        self.ctl.load("src/ndnSIM/NFD/daemon/table/framework/program.lp")

    def get_action(self, cache, package):
        # Set all atoms of the currently considered window (see section
        # "Optimization-> Windowing" in the main document for more information)
        # For CCN these atoms are not encoded via MSS but directly into the
        # program
        self.set_clingo_externals(cache, package)
        self.ctl.ground([("base", [])], context=self)
        self.ctl.solve(on_model=self.on_model)
        action = self.action[0][1]
        return action

    def set_clingo_externals(self, cache, package):
        # add the disjunctive action rule
        action_string = ''
        for a in range(self.size):
            action_string += f'action(T, {a})'
            if a < self.size - 1:
                action_string += f' | '
        action_string += f' :- T = 0..horizon - 1.'
        self.ctl.add("base", [], action_string)

        # add the guessing rule for incoming packages
        inc_string = ''
        for p in range(len(self.prefixes)):
            inc_string += f'inc_cell(T, {p})'
            if p < len(self.prefixes) - 1:
                inc_string += f' | '
        inc_string += f' :- T = 1..horizon.'

        # encode which packages are low/high prio
        for p in self.low_prio:
            self.ctl.add("base", [], f"low_prio({p}).")
        for p in self.high_prio:
            self.ctl.add("base", [], f"high_prio({p}).")

        # encode the current cache content
        for i, cell in enumerate(cache.packages):
            prefix = -1
            for j, p in enumerate(self.prefixes):
                if cell.startswith(p):
                    prefix = j

            self.ctl.add("base", [], f"cell_content({0},{i},{prefix}).")
            time_diff = cache.time - cache.added[i]
            self.ctl.add("base", [], f"cell_age({0},{i},{time_diff}).")


            actions = np.copy(cache.last_used)
            actions = list(np.argsort(actions))
            self.ctl.add("base", [], f"ranking({i},{actions.index(i)}).")
        self.ctl.add("base", [], f"ranking({self.size},{self.size}).")
        prefix = -1
        for j, p in enumerate(self.prefixes):
            if package.startswith(p):
                prefix = j
        self.ctl.add("base", [], f"inc_cell({0},{prefix}).")
