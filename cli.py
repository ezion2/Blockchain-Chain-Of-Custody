import argparse
import os
from parser import *


class Parser:

    def build_args(self):
        """
        Constructs command line arguments for the chain-of-custody tool
        """
        parser = argparse.ArgumentParser(description="Parser for chain-of-custody tool")
        subparsers = parser.add_subparsers()
        bchoc = subparsers.add_parser("bchoc", help="Chain of custody")
        options = bchoc.add_subparsers()

        add = options.add_parser('add', help='add new case')
        add.set_defaults(func=add_case)
        add.add_argument('-c', dest='case_id', help="Enter case ID")
        add.add_argument('-i', dest='item_id', help="Enter item ID", action='append')

        checkout_parser = options.add_parser('checkout', help='checkout a case')
        checkout_parser.set_defaults(func=checkout)
        checkout_parser.add_argument('-i', dest='item_id', help="Enter item ID")

        checkin_parser = options.add_parser('checkin', help='checkin a case')
        checkin_parser.set_defaults(func=checkin)
        checkin_parser.add_argument('-i', dest='item_id', help="Enter item ID")

        log_parser = options.add_parser('log', help='log a case or cases')
        log_parser.set_defaults(func=log)
        log_parser.add_argument('-n', dest='num_entries', help="Enter number of entries to log")
        log_parser.add_argument('-c', dest='case_id', help="Enter the case ID")
        log_parser.add_argument('-i', dest='item_id', help="Enter the item ID")
        log_parser.add_argument('-r', dest='reverse', help="Reverses the order of the block entries to show the most recent entries first.")

        removal_parser = options.add_parser('remove', help='remove a case')
        removal_parser.set_defaults(func=remove)
        removal_parser.add_argument('-y', dest='reason', help="Enter reason for removal")
        removal_parser.add_argument('-o', dest='owner', help="Enter name of owner")
        removal_parser.add_argument('-i', dest='item_id', help="Enter the item ID")

        init_parser = options.add_parser('init', help='Initialize Blockchain')
        init_parser.set_defaults(func=initialize_blockchain)

        verify_parser = options.add_parser('verify', help='Verify Blockchain')
        verify_parser.set_defaults(func=verify_blockchain)

        arguments = parser.parse_args()
        arguments.func(arguments)


if __name__ == '__main__':
    parse = Parser()
    parse.build_args()