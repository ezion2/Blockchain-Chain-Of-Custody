import subprocess as sp
from blockchain import Blockchain
import struct
import sys
import datetime
import hashlib
import uuid

def add_case(args):
    # Check to see if we got a valid UUID
    try:
        case_uuid = uuid.UUID(args.case_id)
    except ValueError:
        print("Invalid UUID format! Terminating...")
        sys.exit(1)

    blockchain = Blockchain(False)

    #check if item id exists
    for item in args.item_id:
        for block in blockchain.chain:
            block_item_id = struct.unpack('I', block.item_id)[0]
            if block_item_id == int(item):
                print('Item already in chain! Terminating...')
                sys.exit(1)

    #print case and newly added items
    print('Case: ', case_uuid)
    for item in args.item_id:
        blockchain.add_block(args.case_id.replace("-", ""), item)


def checkout(args):
    found = False
    blockchain = Blockchain(False)
    # check if item id exists
    for item in args.item_id:
        for block in blockchain.chain:
            block_item_id = struct.unpack('I', block.item_id)[0]
            if block_item_id == int(item):
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
            if block_item_id == int(item):
                blockchain.check_in(args.item_id)
                found = True
                break
    if found is False:
        print('Item not found in block...')
        sys.exit(1)

def log(args):
    # To store all our entries
    entries = []
    with open("blockchain_file", "rb") as file:
        # Reading the initial block, we need to log it
        initial_chunk = file.read(90)
        initial_block_caseID = str(uuid.UUID("00000000000000000000000000000000"))
        initial_block_itemID = int.from_bytes(initial_chunk[56:60], byteorder="little")
        initial_block_action = initial_chunk[60:72].decode().replace('\x00', '')
        initial_block_timestamp = datetime.datetime.fromtimestamp(struct.unpack("<d",initial_chunk[32:40])[0]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

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
            caseID = str(uuid.UUID(hex(int.from_bytes(entry[40:56], byteorder="big"))[2:].upper()))
            itemID = int.from_bytes(entry[56:60], byteorder="little")
            action = entry[60:72].decode().replace('\x00', '')
            timestamp = datetime.datetime.fromtimestamp(struct.unpack("<d",entry[32:40])[0]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            entries.append((caseID, itemID, action, timestamp))

    # Filter based on caseID
    entries = caseID_Filter(entries, args)
    # Filter based on itemID
    entries = itemID_Filter(entries, args)

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
            logCaseID = str(uuid.UUID(args.case_id))
        except ValueError:
            print("Invalid UUID format!")
            sys.exit(1)

        for tuple in array[:]:
            if logCaseID not in tuple:
                array.remove(tuple)
    return array

# Method to assist in the functionality of the log and verify function.
def itemID_Filter(array, args=None):
    # Filter based on itemID
    if args.item_id != None:
        for tuple in array[:]:
            if int(args.item_id) not in tuple:
                array.remove(tuple)
    return array



def remove(args):
    print(f"{args.item_id}")


def initialize_blockchain(args):
    blockchain = Blockchain(True)

def verify_blockchain(args):
        # To store all our entries
    entries = []
    with open("blockchain_file", "rb") as file:
        # Skipping the initial block, we need not log it
        chunk = file.read(90)
        # initial_block_sha256 = hashlib.sha256(chunk).hexdigest()
        # hashin = hashlib.sha256(pickle.dumps(chunk)).hexdigest()

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
            #parent_block_hash = hex(int.from_bytes(entry[0:32],byteorder='big'))[2:].upper()
            parent_block_hash = int.from_bytes(entry[0:32],byteorder='big')
            caseID = uuid.UUID(hex(int.from_bytes(entry[40:56], byteorder="big"))[2:].upper())
            itemID = int.from_bytes(entry[56:60], byteorder="little")
            action = entry[60:72].decode().replace('\x00', '')
            timestamp = datetime.datetime.fromtimestamp(struct.unpack("<d",entry[32:40])[0]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            # Computing the sha256 hash for each individual block
            blocksha256 = hashlib.sha256(entry).hexdigest().upper()

            entries.append((parent_block_hash, blocksha256, caseID, itemID, action, timestamp))
    
    print("Transactions in blockchain: {0}".format(len(entries)))
    # There can be only 1 error at a time
    # Filtering process
    # Check if we have a parent block
    for blockEntry in entries:
        if len(hex(blockEntry[0])[2:].upper()) == 1 or blockEntry[0] == 0:
            print("State of blockchain: ERROR\nBad block: {0}\nParent block: NOT FOUND".format(blockEntry[1]))
            return

    # Check if two blocks were found with the same parent.
    parentsHashes = [hashList[0] for hashList in entries]
    # Going in reverse since I assume that the block that would have the same parent would be later down the list
    for i in range(len(parentsHashes)-1, -1, -1):
        if parentsHashes.count(parentsHashes[i]) > 1:
            parentBlock = hex(parentsHashes[i])[2:].upper()
            print("State of blockchain: ERROR\nBad block: {0}\nParent block: {1}\nTwo blocks were found with the same parent.".format(entries[i][1], parentBlock))
            return
    
    # Now checking to see if the sha-256 hash present in the block data, matches with the ????
    #for blockEntry in entries:
    #    if len(hex(blockEntry[0])[2:].upper()) == 1 or blockEntry[0] == 0:
    #        print("State of blockchain: ERROR\nBad block: {0}\nBlock contents do not match block checksum.".format(blockEntry[1]))
    #        return

    # Check to see if an item has been checked out or checked in after removal from chain.
    # Check for an item id that has more than one entry
    
    print("State of blockchain: CLEAN")
    #for i in entries:
    #    print(i[2])