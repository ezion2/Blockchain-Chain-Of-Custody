import argparse

from parser import block_chain


class Parser:

    def build_args(self):
        """
        Constructs command line arguments for the chain-of-custody tool
        """
        parser = argparse.ArgumentParser(
            description="Parser for chain-of-custody tool"
        )
        parser.add_argument(
            "--no-banner",
            action="store_true",
            default=False,
            dest="no_banner",
            help="Do not display banner",
        )
        subparsers = parser.add_subparsers()
        chain = subparsers.add_parser('bchoc', help='Block-Chain-of-Custody')
        chain.set_defaults(func=block_chain)

        return parser.parse_args()