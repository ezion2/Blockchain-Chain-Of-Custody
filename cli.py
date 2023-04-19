import argparse
import os
import os.path
import hashlib
import struct
import sys
import time, datetime
import uuid
import subprocess as sp


class Parser:

    def build_args(self):
        """
        Constructs command line arguments for the chain-of-custody tool
        """
        parser = argparse.ArgumentParser(description="Parser for chain-of-custody tool")
        subparsers = parser.add_subparsers()

        add = subparsers.add_parser('add', help='add new case')
        add.set_defaults(func=add_case)
        add.add_argument('-c', dest='case_id', help="Enter case ID")
        add.add_argument('-i', dest='item_id', help="Enter item ID", action='append')

        checkout_parser = subparsers.add_parser('checkout', help='checkout a case')
        checkout_parser.set_defaults(func=checkout)
        checkout_parser.add_argument('-i', dest='item_id', help="Enter item ID")

        checkin_parser = subparsers.add_parser('checkin', help='checkin a case')
        checkin_parser.set_defaults(func=checkin)
        checkin_parser.add_argument('-i', dest='item_id', help="Enter item ID")

        log_parser = subparsers.add_parser('log', help='log a case or cases')
        log_parser.set_defaults(func=log)
        log_parser.add_argument('-n', dest='num_entries', help="Enter number of entries to log")
        log_parser.add_argument('-c', dest='case_id', help="Enter the case ID")
        log_parser.add_argument('-i', dest='item_id', help="Enter the item ID")
        log_parser.add_argument('-r', '--reverse', dest='reverse', action='store_true', help="Reverses the order of the block entries to show the most recent entries first.")

        removal_parser = subparsers.add_parser('remove', help='remove a case')
        removal_parser.set_defaults(func=remove)
        removal_parser.add_argument('-y', '--why', dest='reason', help="Enter reason for removal")
        removal_parser.add_argument('-o', dest='owner', help="Enter name of owner")
        removal_parser.add_argument('-i', dest='item_id', help="Enter the item ID")

        init_parser = subparsers.add_parser('init', help='Initialize Blockchain')
        init_parser.set_defaults(func=initialize_blockchain)

        verify_parser = subparsers.add_parser('verify', help='Verify Blockchain')
        verify_parser.set_defaults(func=verify_blockchain)

        arguments = parser.parse_args()
        arguments.func(arguments)


def add_case(args):
    # Check to see if we got a valid UUID
    try:
        if(args.case_id):
            case_uuid = uuid.UUID(args.case_id)
        else:
            sys.exit(1)
    except ValueError:
        print("Invalid UUID format! Terminating...")
        sys.exit(1)
    if(os.path.isfile(BCF)):
        blockchain = Blockchain(False)
        block = True
    else:
        blockchain = Blockchain(False)
        block = False
    # check if item id exists
    if(args.item_id and args.case_id):
        for item in args.item_id:
            for block in blockchain.chain:
                block_item_id = struct.unpack('I', block.item_id)[0]
                if block_item_id == int(item):
                    print('Item already in chain! Terminating...')
                    sys.exit(1)

        # print case and newly added items
        print('Case: ', case_uuid)
        for item in args.item_id:
            blockchain.add_block(args.case_id.replace("-", ""), item, block)
    else:
        sys.exit(1)



def checkout(args):
    found = False
    blockchain = Blockchain(False)
    # check if item id exists
    for item in args.item_id:
        for block in blockchain.chain:
            block_item_id = struct.unpack('I', block.item_id)[0]
            if int(block_item_id) == int(args.item_id) and found is False:
                blockchain.check_out(args.item_id)
                found = True
                break
    if found is False:
        print('Item not found in block...')
        sys.exit(1)


def checkin(args):
    found = False
    blockchain = Blockchain(False)
    # check if item id exists
    for item in args.item_id:
        for block in blockchain.chain:
            block_item_id = struct.unpack('I', block.item_id)[0]
            if int(block_item_id) == int(args.item_id) and found is False:
                blockchain.check_in(args.item_id)
                found = True
                break
    if found is False:
        print('Item not found in block...')
        sys.exit(1)


def log(args):
    # To store all our entries
    entries = []
    with open(BCF, "rb") as file:
        # Reading the initial block, we need to log it
        initial_chunk = file.read(90)
        initial_block_caseID = str(uuid.UUID("00000000000000000000000000000000"))
        initial_block_itemID = int.from_bytes(initial_chunk[56:60], byteorder="little")
        initial_block_action = initial_chunk[60:72].decode().replace('\x00', '')
        initial_block_timestamp = datetime.datetime.fromtimestamp(
            struct.unpack("<d", initial_chunk[32:40])[0]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        entries.append((initial_block_caseID, initial_block_itemID, initial_block_action, initial_block_timestamp))

        # Loop indefinitely until chunk is empty.
        while True:
            # Read in fixed chunk size
            chunk1 = file.read(76)

            # If the first half is missing, we've reached end of file
            if not chunk1:
                break

            # Find out how long the string part of the entry is since it is variable sized
            dataLength = struct.unpack("<I", chunk1[72:76])[0]
            length = "{0}s".format(dataLength)
            # Read it out
            chunk2 = struct.unpack(length, file.read(dataLength))[0]

            # Combine the two chunks creating our entry
            entry = chunk1 + chunk2

            # Appending entry
            # Fixing missing leading zeros
            part1 = hex(int.from_bytes(entry[40:56], byteorder="little"))[2:]
            if len(part1) < 32:
                leadingZeros = 32 - len(part1)
                for i in range(leadingZeros):
                    part1 = "0"+part1
            caseID = str(uuid.UUID(part1))
            itemID = int.from_bytes(entry[56:60], byteorder="little")
            action = entry[60:72].decode().replace('\x00', '')
            timestamp = datetime.datetime.fromtimestamp(struct.unpack("<d", entry[32:40])[0]).strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ')

            entries.append((caseID, itemID, action, timestamp))

    # Filter based on caseID
    entries = caseID_Filter(entries, args)
    # Filter based on itemID
    entries = itemID_Filter(entries, args.item_id)

    # index i to allow us to print how many entries is required
    # if args.num_entries is set to None then we will be able to print out ever entry in the blockchain
    # if it is set to a value then i will increment up to that value and then break out of the loop
    i = 0

    # Since it is not set, set its length to the number of entries
    if args.num_entries == None:
        args.num_entries = len(entries)

    if args.reverse == True:
        for log in reversed(entries):
            if int(args.num_entries) == i:
                break
            print("Case: {0}\nItem: {1}\nAction: {2}\nTime: {3}\n".format(log[0], log[1], log[2], log[3]))
            i = i + 1
    else:
        for log in entries:
            if int(args.num_entries) == i:
                break
            print("Case: {0}\nItem: {1}\nAction: {2}\nTime: {3}\n".format(log[0], log[1], log[2], log[3]))
            i = i + 1


# Method to assist in the functionality of the log and verify function.
def caseID_Filter(array, args=None):
    if args.case_id != None:
        # Check to see if we got a valid UUID
        try:
            # Convert it to a uuid (to get the formatting) and then back to string (so we can do comparisons also because I left it in the uuid format)
            logCaseID = str(uuid.UUID(args.case_id[::1]))
        except ValueError:
            print("Invalid UUID format!")
            sys.exit(1)

        for tuple in array[:]:
            if logCaseID not in tuple:
                array.remove(tuple)
    return array


# Method to assist in the functionality of the log and verify function.
def itemID_Filter(array, args=None, verify=False):
    # Filter based on itemID
    if verify == False:
        if args != None:
            for tuple in array[:]:
                if int(args) not in tuple:
                    array.remove(tuple)
        return array
    else:
        # index
        i = 0
        validIndex = []
        if args != None:
            for tuple in array[:]:
                if int(args) in tuple:
                    validIndex.append(i)
                    i = i + 1
            # Removal
            for tuple in array[:]:
                if int(args) not in tuple:
                    array.remove(tuple)
        return (array, validIndex)


def remove(args):
    found = False
    blockchain = Blockchain(False)
    # check if item id exists
    for item in args.item_id:
        for block in blockchain.chain:
            block_item_id = struct.unpack('I', block.item_id)[0]
            if int(block_item_id) == int(args.item_id) and found is False:
                blockchain.remove(args.item_id, args.reason, args.owner)
                found = True
                break
    if found is False:
        print('Item not found in block...')
        sys.exit(1)


def initialize_blockchain(args):
    blockchain = Blockchain(True)


def verify_blockchain(args):
    # To store all our entries
    entries = []
    with open(BCF , "rb") as file:
        # Reading the initial block
        initial_chunk = file.read(90)
        initial_block_parent_block_hash = int.from_bytes(initial_chunk[0:32],byteorder='big')
        initial_block_sha256 = hashlib.sha256(initial_chunk).hexdigest()
        initial_block_caseID = str(uuid.UUID("00000000000000000000000000000000"))
        initial_block_itemID = int.from_bytes(initial_chunk[56:60], byteorder="little")
        initial_block_action = initial_chunk[60:72].decode().replace('\x00', '')
        initial_block_timestamp = datetime.datetime.fromtimestamp(struct.unpack("<d",initial_chunk[32:40])[0]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        entries.append([initial_block_parent_block_hash, initial_block_sha256, initial_block_caseID, initial_block_itemID, initial_block_action, initial_block_timestamp])

        # Loop indefinitely until chunk is empty.
        while True:
            # Read in fixed chunk size
            chunk1 = file.read(76)

            # If the first half is missing, we've reached end of file
            if not chunk1:
                break

            # Find out how long the string part of the entry is since it is variable sized
            dataLength = struct.unpack("<I", chunk1[72:76])[0]
            length = "{0}s".format(dataLength)
            # Read it out
            chunk2 = struct.unpack(length, file.read(dataLength))[0]

            # Combine the two chunks creating our entry
            entry = chunk1 + chunk2

            # Appending entry
            parent_block_hash = int.from_bytes(entry[0:32], byteorder='big')
            # Fix leading zero issue
            part1 = hex(int.from_bytes(entry[40:56], byteorder="big"))[2:]
            if len(part1) < 32:
                leadingZeros = 32 - len(part1)
                for i in range(leadingZeros):
                    part1 = "0"+part1
            caseID = str(uuid.UUID(part1))
            itemID = int.from_bytes(entry[56:60], byteorder="little")
            action = entry[60:72].decode().replace('\x00', '')
            timestamp = datetime.datetime.fromtimestamp(struct.unpack("<d", entry[32:40])[0]).strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ')

            # Computing the sha256 hash for each individual block
            blocksha256 = hashlib.sha256(entry).hexdigest()

            entries.append([parent_block_hash, blocksha256, caseID, itemID, action, timestamp])

    print("Transactions in blockchain: {0}".format(len(entries)))
    # There can be only 1 error at a time
    # Filtering process
    # Check if we have a parent block
    for blockEntry in entries:
        if len(hex(blockEntry[0])[2:]) == 1 or blockEntry[0] == 0:
            print("State of blockchain: ERROR\nBad block: {0}\nParent block: NOT FOUND".format(blockEntry[1]))
            sys.exit(1)

    # Check if two blocks were found with the same parent.
    parentsHashes = [hashList[0] for hashList in entries]
    # Going in reverse since I assume that the block that would have the same parent would be later down the list
    for i in range(len(parentsHashes) - 1, -1, -1):
        if parentsHashes.count(parentsHashes[i]) > 1:
            parentBlock = hex(parentsHashes[i])[2:]
            print(
                "State of blockchain: ERROR\nBad block: {0}\nParent block: {1}\nTwo blocks were found with the same parent.".format(
                    entries[i][1], parentBlock))
            sys.exit(1)

    # Now checking to see if the sha-256 hash for the current block matches the parent sha-256 hash of the next block
    for i in range(len(entries) - 1):
        if entries[i][1] != hex(entries[i+1][0])[2:]:
            print("State of blockchain: ERROR\nBad block: {0}\nBlock contents do not match block checksum.".format(blockEntry[1]))
            sys.exit(1)

    # Check to see if an item has been checked out or checked in after removal from chain.
    itemIDS  = [hashList[3] for hashList in entries]
    removalCheck(itemIDS, entries)

    print("State of blockchain: CLEAN")

# To help with verify function
def removalCheck(itemIDS, entries):
    # Base case
    # Check if list is empty
    removalFlag = False
    if len(itemIDS) == 0:
        return
    else:
        removalFlag = False
        # Loop
        while itemIDS:
            # If this item does not have more than 1 entry, remove it
            if itemIDS.count(itemIDS[0]) < 2:
                itemIDS.pop(0)
                entries.pop(0)
            # If this item has more than 1 entry, check all entries with said item ID
            elif itemIDS.count(itemIDS[0]) > 1:
                # Make a copy of entries
                entryCopy = entries.copy()
                entryCopy = itemID_Filter(entryCopy, itemIDS[0], True)
                # Loop through this copy, check to see if an item has been checked out or checked in after removal from chain.
                for entry in entryCopy[0]:
                    if entry[4] == 'DISPOSED' or entry[4] == 'RELEASED' or entry[4] == 'DESTROYED':
                        removalFlag = True
                    if entry[4] == 'CHECKEDIN' or entry[4] == 'CHECKEDOUT':
                        if removalFlag == True:
                            print("State of blockchain: ERROR\nBad block: {0}\nItem checked out or checked in after removal from chain.".format(entry[1]))
                            sys.exit(1)
                removalFlag = False
                # Remove the values we have found from entries
                shift = 0
                for i in range(len(entryCopy[1])):
                    # take into account shifting position
                    entries.pop(entryCopy[1][i] - shift)
                    itemIDS.pop(entryCopy[1][i] - shift)
                    shift = shift + 1


# blockchain file name
BCF = os.environ.get('BCHOC_FILE_PATH')


# Class to construct individual blocks
class Block:
    # packages each variable into byte literal of desired size
    def __init__(self, previous_hash, timeStamp, case_id, item_id, state, data_length, data):
        self.previous_hash = struct.pack('32s', previous_hash)
        self.timeStamp = struct.pack('d', timeStamp)
        self.case_id = struct.pack('16s', case_id)
        self.item_id = struct.pack('I', item_id)
        self.state = struct.pack('12s', state)
        self.data_length = struct.pack('I', data_length)
        self.data = struct.pack((str(data_length) + 's'), data)


# Class to construct full blockchain data structure
class Blockchain:
    # builds blockchain based on blockchain file. 'display' bool prints blockchain file status if true
    def __init__(self, display):
        try:
            with open(BCF, 'rb') as f:
                self.chain = []

                # loops until EOF
                while True:
                    # reads bytes and converts to desired data type to build blockchain data structure
                    next = f.read(32)
                    if next == b'': break
                    previous_hash = struct.unpack('32s', next)
                    timeStamp = struct.unpack('d', f.read(8))
                    case_id = struct.unpack('16s', f.read(16))
                    item_id = struct.unpack('I', f.read(4))
                    state = struct.unpack('12s', f.read(12))
                    data_length = struct.unpack('I', f.read(4))
                    data = struct.unpack((str(data_length[0]) + 's'), f.read(data_length[0]))

                    # creates block and appends to end of chain
                    read_block = Block(previous_hash[0], timeStamp[0], case_id[0], item_id[0], state[0], data_length[0],
                                       data[0])
                    self.chain.append(read_block)

            if display:
                print('Blockchain file found with INITIAL block.')

        # if blockchain file not found create initial node
        except FileNotFoundError:
            self.chain = [self.create_initial_block()]
            self.add_to_file(self.chain[0])

            if display:
                print('Blockchain file not found. Created INITIAL block.')

                # creates initial block

    def create_initial_block(self):
        initial_block = Block(b'', time.time(), b'', 0, b'INITIAL', 14, b'Initial block')
        return initial_block

    # get latest block added to the chain
    def get_latest_block(self):
        return self.chain[-1]

    # adds block to blockchain file
    def add_to_file(self, block):
        with open(BCF, 'ab') as f:
            f.write(block.previous_hash)
            f.write(block.timeStamp)
            f.write(block.case_id)
            f.write(block.item_id)
            f.write(block.state)
            f.write(block.data_length)
            f.write(block.data)

    # time conversion function (INCOMPLETE)
    def utcEpoch_to_localISO(self, epoch):
        utc_datetime = datetime.datetime.utcfromtimestamp(epoch)
        local_iso = utc_datetime.isoformat()
        return local_iso

    # add block to blockchain data structure
    def add_block(self, case_id, item_id, block):
        # creates new block and adds to chain
        # Computing the hash on the data itself, not the object
        # The hash is the hex value, not the ascii representation, lets us fit all 64 characters in the file without going over byte limit
        # previous_data = self.get_latest_block().previous_hash + self.get_latest_block().timeStamp + self.get_latest_block().case_id + self.get_latest_block().item_id + self.get_latest_block().state + self.get_latest_block().data_length + self.get_latest_block().data
        # previous_hash_byt = hashlib.sha256(previous_data).digest()
        # new_block = Block(previous_hash_byt, time.time(), bytes.fromhex(case_id), int(item_id), b'CHECKEDIN', 5,
        #                   b'None')
        if(block is False):
            previous_data = self.get_latest_block().previous_hash + self.get_latest_block().timeStamp + self.get_latest_block().case_id + self.get_latest_block().item_id + self.get_latest_block().state + self.get_latest_block().data_length + self.get_latest_block().data
            previous_hash_byt = hashlib.sha256(previous_data).digest()
            new_block = Block(b'', time.time(), bytes(bytearray.fromhex(case_id)[::-1]), int(item_id), b'CHECKEDIN', 5,
                              b'')
            self.chain.append(new_block)
            self.add_to_file(new_block)
        else:
            previous_data = self.get_latest_block().previous_hash + self.get_latest_block().timeStamp + self.get_latest_block().case_id + self.get_latest_block().item_id + self.get_latest_block().state + self.get_latest_block().data_length + self.get_latest_block().data
            previous_hash_byt = hashlib.sha256(previous_data).digest()
            new_block = Block(previous_hash_byt, time.time(), bytes(bytearray.fromhex(case_id)[::-1]), int(item_id), b'CHECKEDIN', 0,
                              b'')
            self.chain.append(new_block)
            self.add_to_file(new_block)


        # prepare for output
        state_str = (struct.unpack('12s', new_block.state)[0]).decode()
        item_id_int = struct.unpack('I', new_block.item_id)[0]
        utc_epoch = struct.unpack('d', new_block.timeStamp)[0]
        iso_str = self.utcEpoch_to_localISO(utc_epoch)

        # output format and print
        new_block_str = 'Added item: {0} \n\tStatus: {1} \n\tTime of action: {2}'.format(item_id_int, state_str,
                                                                                         iso_str)
        print(new_block_str)

    def check_in(self, item_id):
        """Searches blockchain for a given case and checks it in otherwise exits program with error"""
        found = False
        # Looping in reverse, since latest additions to the block will be found at the end presumably
        for block in reversed(self.chain):
            blockItemID = str(struct.unpack('I', block.item_id)[0])
            if blockItemID == item_id:
                blockItemAction = struct.unpack('12s', block.state)[0].decode().replace('\x00', '')
                if blockItemAction == 'CHECKEDOUT' and found is False:
                    # Computing the hash on the data itself
                    # The hash is the hex value, not the ascii representation, lets us fit all 64 characters in the file without going over byte limit
                    previous_data = self.get_latest_block().previous_hash + self.get_latest_block().timeStamp + self.get_latest_block().case_id + self.get_latest_block().item_id + self.get_latest_block().state + self.get_latest_block().data_length + self.get_latest_block().data
                    previous_hash_byt = hashlib.sha256(previous_data).digest()
                    # Block Case is stored as base 16 uuid, stored as hex values not the ascii representation, letting us have acccess to all 32 characters with only 16 bytes
                    # Fixes the string to have leading zeros if the caseID has them
                    # Fixes the string to have leading zeros if the caseID has them
                    part1 = hex(int.from_bytes(block.case_id, byteorder="big"))[2:]
                    if len(part1) < 32:
                        leadingZeros = 32 - len(part1)
                        for i in range(leadingZeros):
                            part1 = "0"+part1
                    blockCaseID = bytes.fromhex(part1)
                    new_block = Block(previous_hash_byt, time.time(), block.case_id[::1], int(item_id), b'CHECKEDIN', 0,
                                      b'')
                    self.chain.append(new_block)
                    self.add_to_file(new_block)
                    state_str = (struct.unpack('12s', new_block.state)[0]).decode()
                    item_id_int = struct.unpack('I', new_block.item_id)[0]
                    utc_epoch = struct.unpack('d', new_block.timeStamp)[0]
                    iso_str = self.utcEpoch_to_localISO(utc_epoch)
                    self.print_check(uuid.UUID(bytes.hex(block.case_id[::-1])), state_str, item_id_int, utc_epoch, iso_str,
                                     'Checked in item')
                    found = True
                    break
                elif struct.unpack('12s', block.state)[0].decode().replace('\x00', '') == 'CHECKEDIN' and found is False:
                    print("Error: Cannot check in an item that has already been checked in.")
                    sys.exit(1)

    def check_out(self, item_id):
        """Searches blockchain for a given case
        and checks if is not already checked out,
        if not it will proceed with checkout otherwise exits program with error"""
        found = False
        # Looping in reverse, since latest additions to the block will be found at the end presumably
        for block in reversed(self.chain):
            blockItemID = str(struct.unpack('I', block.item_id)[0])
            if int(blockItemID) == int(item_id):
                # Have to get rid of null characters at the end
                blockItemAction = struct.unpack('12s', block.state)[0].decode().replace('\x00', '')
                if blockItemAction == "CHECKEDIN" and found is False:
                    # Computing the hash on the data itself
                    # The hash is the hex value, not the ascii representation, lets us fit all 64 characters in the file without going over byte limit
                    previous_data = self.get_latest_block().previous_hash + self.get_latest_block().timeStamp + self.get_latest_block().case_id + self.get_latest_block().item_id + self.get_latest_block().state + self.get_latest_block().data_length + self.get_latest_block().data
                    previous_hash_byt = hashlib.sha256(previous_data).digest()
                    # Block Case is stored as base 16 uuid, stored as hex values not the ascii representation, letting us have acccess to all 32 characters with only 16 bytes
                    # Fixes the string to have leading zeros if the caseID has them
                    part1 = hex(int.from_bytes(block.case_id, byteorder="big"))[2:]
                    if len(part1) < 32:
                        leadingZeros = 32 - len(part1)
                        for i in range(leadingZeros):
                            part1 = "0"+part1
                    blockCaseID = bytes.fromhex(part1)
                    new_block = Block(previous_hash_byt, time.time(), block.case_id[::1], int(item_id), b'CHECKEDOUT', 0,
                                      b'')
                    self.chain.append(new_block)
                    self.add_to_file(new_block)
                    state_str = (struct.unpack('12s', new_block.state)[0]).decode()
                    item_id_int = struct.unpack('I', new_block.item_id)[0]
                    utc_epoch = struct.unpack('d', new_block.timeStamp)[0]
                    iso_str = self.utcEpoch_to_localISO(utc_epoch)
                    self.print_check(uuid.UUID(bytes.hex(block.case_id[::-1])), state_str, item_id_int, utc_epoch, iso_str,
                                     'Checked out item')
                    found = True
                    break
                else:
                    print("Error: Cannot check out a checked out item. Must check it in first.")
                    sys.exit(1)

    def remove(self, item_id, reason, owner=None):
        # search through blockchain for entered item_ID
        # Throw error if not found DONE
        # If status is already REMOVED, fail DONE
        # if status is checked out, fail DONE
        # else, continue remove operation
        # Write over the removed block
        # at end, print removed data DONE
        # Check for -o if reason is released?
        for block in reversed(self.chain):
            blockItemID = str(struct.unpack('I', block.item_id)[0])
            if blockItemID == item_id:
                blockItemAction = struct.unpack('12s', block.state)[0].decode().replace('\x00', '')
                if blockItemAction == 'CHECKEDOUT':
                    print("Error: Cannot remove a checked out item.")
                    sys.exit(1)
                elif blockItemAction == 'DISPOSED' or blockItemAction == 'RELEASED' or blockItemAction == 'DESTROYED':
                    print("Error: Cannot remove an item that has already been removed.")
                    sys.exit(1)
                elif blockItemAction == 'CHECKEDIN':  # MUST BE CHECKED IN TO SUCCEED
                    # Check for given reason of removal
                    # Must be one of: DISPOSED, DESTROYED, or RELEASED
                    if reason == 'DISPOSED' or reason == 'RELEASED' or reason == 'DESTROYED':
                        # Now check if we got RELEASED and make sure and owner is specified
                        if reason == 'RELEASED' and owner is None:
                            print(
                                "Error: Information about the lawful owner to whom the evidence belongs to must be given.")
                            sys.exit(1)
                        # Computing the hash on the data itself
                        # The hash is the hex value, not the ascii representation, lets us fit all 64 characters in the file without going over byte limit
                        reason = reason.encode()
                        previous_data = self.get_latest_block().previous_hash + self.get_latest_block().timeStamp + self.get_latest_block().case_id + self.get_latest_block().item_id + self.get_latest_block().state + self.get_latest_block().data_length + self.get_latest_block().data
                        previous_hash_byt = hashlib.sha256(
                            previous_data).digest()  # MUST WRITE OVER THE FOUND BLOCK, CHANGE STATUS TO THAT OF COMMAND
                        # Block Case is stored as base 16 uuid, stored as hex values not the ascii representation, letting us have acccess to all 32 characters with only 16 bytes
                        part1 = hex(int.from_bytes(block.case_id, byteorder="big"))[2:]
                        if len(part1) < 32:
                            leadingZeros = 32 - len(part1)
                            for i in range(leadingZeros):
                                part1 = "0"+part1
                        blockCaseID = bytes.fromhex(part1)
                        if owner is None:
                            new_block = Block(previous_hash_byt, time.time(), blockCaseID, int(item_id), reason, 0, b'')
                        else:
                            new_block = Block(previous_hash_byt, time.time(), blockCaseID, int(item_id), reason, (len(owner) + 1), owner.encode())
                        self.chain.append(new_block)
                        self.add_to_file(new_block)
                        utc_epoch = struct.unpack('d', new_block.timeStamp)[0]
                        iso_str = self.utcEpoch_to_localISO(utc_epoch)

                        print("Case: {0}\nRemoved item: {1}\n\tStatus: {2}".format(uuid.UUID(bytes.hex(block.case_id[::-1])),
                                                                                   item_id[0], reason.decode()))
                        if owner != None:
                            print("\tOwner info:", owner)
                        print("\tTime: ", iso_str)
                        break
                    else:
                        print("Error: Invalid reason given.")
                        sys.exit(1)

    def print_check(self, case, state, item_id, utc_epoch, iso_str, action_str):
        new_block_str = f'Case: {case} \n{action_str}: {item_id} \n\tStatus: {state} \n\tTime of action: {iso_str}'
        print(new_block_str)
if __name__ == '__main__':
    parse = Parser()
    parse.build_args()