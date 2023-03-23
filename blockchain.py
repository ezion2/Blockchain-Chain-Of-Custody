import hashlib
import json
from enum import Enum

class State(enum):
    INITIAL = 0
    CHECKEDIN = 1
    CHECKEDOUT = 2
    DISPOSED = 3
    DESTROYED = 4
    RELEASED = 5





class Block:
    def __init__(self, previous_hash, timeStamp, case_id, item_id, state, data_length, data):
        self.previous_hash = previous_hash
        self.timeStamp =timeStamp
        self.case_id - case_id
        self.item_id = item_id
        self.state = state
        self.data_length = data_length
        self.data = data
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_str = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()