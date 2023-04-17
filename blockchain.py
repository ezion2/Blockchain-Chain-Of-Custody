#necessary libraries
import hashlib
import struct
import pickle
import sys
import time, datetime

#blockchain file name
BCF = 'blockchain_file'

#Class to construct individual blocks
class Block:
    #packages each variable into byte literal of desired size
    def __init__(self, previous_hash, timeStamp, case_id, item_id, state, data_length, data):
        self.previous_hash = struct.pack('32s', previous_hash)
        self.timeStamp = struct.pack('d', timeStamp)
        self.case_id = struct.pack('16s', case_id)
        self.item_id = struct.pack('I', item_id)
        self.state = struct.pack('12s', state)
        self.data_length = struct.pack('I', data_length)
        self.data = struct.pack((str(data_length) + 's'), data)
        self.hash = self.calculate_hash()

    #calculates sha-256 hash of current block object
    def calculate_hash(self):
        return hashlib.sha256(pickle.dumps(self)).hexdigest()

#Class to construct full blockchain data structure
class Blockchain:
    #builds blockchain based on blockchain file. 'display' bool prints blockchain file status if true
    def __init__(self, display):
        try:
            with open(BCF, 'rb') as f:
                self.chain = []

                #loops until EOF
                while True:
                    #reads bytes and converts to desired data type to build blockchain data structure
                    next = f.read(32)
                    if next == b'': break
                    previous_hash = struct.unpack('32s', next)
                    timeStamp = struct.unpack('d', f.read(8))
                    case_id = struct.unpack('16s', f.read(16))
                    item_id = struct.unpack('I', f.read(4))
                    state = struct.unpack('12s', f.read(12))
                    data_length = struct.unpack('I', f.read(4))
                    data = struct.unpack((str(data_length[0]) + 's'), f.read(data_length[0]))

                    #creates block and appends to end of chain
                    read_block = Block(previous_hash[0], timeStamp[0], case_id[0], item_id[0], state[0], data_length[0], data[0])
                    self.chain.append(read_block)
            
            if display:
                print('Blockchain file found with INITIAL block.')

        #if blockchain file not found create initial node
        except FileNotFoundError:
            self.chain = [self.create_initial_block()]
            self.add_to_file(self.chain[0])
            
            if display:
                print('Blockchain file not found. Created INITIAL block.')  

    #creates initial block
    def create_initial_block(self):
        initial_block = Block(b'None', time.time(), b'None', 0, b'INITIAL', 14, b'Initial Block')
        return initial_block
    
    #get latest block added to the chain
    def get_latest_block(self):
        return self.chain[-1]
    
    #adds block to blockchain file
    def add_to_file(self, block):
        with open(BCF, 'ab') as f:
            f.write(block.previous_hash)
            f.write(block.timeStamp)
            f.write(block.case_id)
            f.write(block.item_id)
            f.write(block.state)
            f.write(block.data_length)
            f.write(block.data)

    #time conversion function (INCOMPLETE)
    def utcEpoch_to_localISO(self, epoch):
        utc_datetime = datetime.datetime.utcfromtimestamp(epoch)
        local_iso = utc_datetime.isoformat()
        return local_iso

    #add block to blockchain data structure
    def add_block(self, case_id, item_id):
        #creates new block and adds to chain
        previous_hash_byt = (self.get_latest_block().hash).encode()
        new_block = Block(previous_hash_byt, time.time(), (case_id).encode(), int(item_id), b'CHECKEDIN', 5, b'None')
        self.chain.append(new_block)
        self.add_to_file(new_block)

        #prepare for output
        state_str = (struct.unpack('12s', new_block.state)[0]).decode()
        item_id_int = struct.unpack('I', new_block.item_id)[0]
        utc_epoch = struct.unpack('d', new_block.timeStamp)[0]
        iso_str = self.utcEpoch_to_localISO(utc_epoch)

        #output format and print
        new_block_str = 'Added item: {0} \n\tStatus: {1} \n\tTime of action: {2}'.format(item_id_int, state_str, iso_str)
        print(new_block_str)
    def check_in(self, item_id):
        """Searches blockchain for a given case and checks it in otherwise exits program with error"""
        for block in self.chain:
            if struct.unpack('I',block.item_id)[0].decode() == item_id:
                previous_hash_byt = self.get_latest_block().hash.encode()
                new_block = Block(previous_hash_byt, time.time(), block.case_id.encode(), int(item_id), b'CHECKEDIN', 5, b'None')
                self.chain.append(new_block)
                self.add_to_file(new_block)
                state_str = (struct.unpack('12s', new_block.state)[0]).decode()
                item_id_int = struct.unpack('I', new_block.item_id)[0]
                utc_epoch = struct.unpack('d', new_block.timeStamp)[0]
                iso_str = self.utcEpoch_to_localISO(utc_epoch)
                self.print_check(block.case_id,state_str,item_id_int,utc_epoch,iso_str,'Checked in item')


    def check_out(self, item_id):
        """Searches blockchain for a given case
        and checks if is not already checked out,
        if not it will proceed with checkout otherwise exits program with error"""
        for block in self.chain:
            if struct.unpack('I', block.item_id)[0].decode() == item_id:
                if struct.unpack('12s', block.state)[0].decode() == 'CHECKEDIN':
                    previous_hash_byt = self.get_latest_block().hash.encode()
                    new_block = Block(previous_hash_byt, time.time(), block.case_id.encode(), int(item_id), b'CHECKEDOUT', 5,b'None')
                    self.chain.append(new_block)
                    self.add_to_file(new_block)
                    state_str = (struct.unpack('12s', new_block.state)[0]).decode()
                    item_id_int = struct.unpack('I', new_block.item_id)[0]
                    utc_epoch = struct.unpack('d', new_block.timeStamp)[0]
                    iso_str = self.utcEpoch_to_localISO(utc_epoch)
                    self.print_check(block.case_id, state_str, item_id_int, utc_epoch, iso_str, 'Checked out item')
                elif struct.unpack('12s', block.state)[0].decode() == 'CHECKEDOUT':
                    print("Error: Cannot check out a checked out item. Must check it in first.")
                    sys.exit(1)

    def print_check(self, case, state, item_id, utc_epoch, iso_str, action_str):
        new_block_str = f'Case: {case} \n{action_str}: {item_id} \n\tStatus: {state} \n\tTime of action: {iso_str}'
        print(new_block_str)
