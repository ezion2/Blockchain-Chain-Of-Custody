import hashlib
import json
import struct

class Block:
    def __init__(self, previous_hash, timeStamp, case_id, item_id, state, data_length, data):
        self.previous_hash = struct.pack('32s', previous_hash)
        self.timeStamp = struct.pack('d', timeStamp)
        self.case_id = struct.pack('16s', case_id)
        self.item_id = struct.pack('I', item_id)
        self.state = struct.pack('12s', state)
        self.data_length = struct.pack('I', data_length)
        self.data = data
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_str = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()