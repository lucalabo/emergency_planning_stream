
class Cache:
    def __init__(self):
        self.packages = []
        self.last_used = []
        self.added = []
        self.time = 0
        self.low_prio_violation = 0
        self.high_prio_violation = 0
        self.interceptions = 0
