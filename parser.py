import subprocess as sp
from blockchain import Blockchain
import struct
import sys

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
    print(f"{args.item_id}")


def remove(args):
    print(f"{args.item_id}")


def initialize_blockchain(args):
    blockchain = Blockchain(True)

def verify_blockchain(args):
    print(f"{args.item_id}")