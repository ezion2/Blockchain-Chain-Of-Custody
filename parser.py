import subprocess as sp
from blockchain import Blockchain
import struct
import sys
import datetime

def add_case(args):
    blockchain = Blockchain(False)
    #check if item id exists
    for item in args.item_id:
        for block in blockchain.chain:
            block_item_id = struct.unpack('I', block.item_id)[0]
            if block_item_id == int(item):
                print('Item already in chain! Terminating...')
                sys.exit(1)

    #print case and newly added items
    print('Case: ', args.case_id)
    for item in args.item_id:
        blockchain.add_block(args.case_id, item)


def checkout(args):
    found = False
    blockchain = Blockchain(False)
    # check if item id exists
    for item in args.item_id:
        for block in blockchain.chain:
            block_item_id = struct.unpack('I', block.item_id)[0]
            if block_item_id == int(item):
                blockchain.check_in(args.item_id)
                found = True
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
    if found is False:
        print('Item not found in block...')
        sys.exit(1)

def log(args):
    # To store all our entries
    entries = []
    with open("blockchain_file", "rb") as file:
        # Skipping the initial block, we need not log it
        file.seek(90)

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
            # Case ID: entry[40:56].decode().replace('\x00', '')
            # Item ID: int.from_bytes(entry[56:60], byteorder="little")
            # State/Action: entry[60:72].decode().replace('\x00', '')
            # Time: datetime.datetime.fromtimestamp(struct.unpack("<d",entry[32:40])[0]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            entries.append((entry[40:56].decode().replace('\x00', ''), int.from_bytes(entry[56:60], byteorder="little"), entry[60:72].decode().replace('\x00', ''), datetime.datetime.fromtimestamp(struct.unpack("<d",entry[32:40])[0]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')))
    
    # Filtering proccess
    # Filter based on caseID
    if args.case_id != None:
        for tuple in entries[:]:
            if args.case_id not in tuple:
                entries.remove(tuple)

    # Filter based on itemID
    if args.item_id != None:
        for tuple in entries[:]:
            if int(args.item_id) not in tuple:
                entries.remove(tuple)

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

    
    


def remove(args):
    print(f"{args.item_id}")


def initialize_blockchain(args):
    blockchain = Blockchain(True)

def verify_blockchain(args):
    print(f"{args.item_id}")
