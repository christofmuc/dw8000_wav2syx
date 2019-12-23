#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

import argparse
from dw8000_wav2syx import dw8000_reverse_engineer


def bin2syx():
    parser = argparse.ArgumentParser(description='Convert a Korg DW8000 bin file converted from tape into syx format')
    parser.add_argument('binfile')
    parser.add_argument('syxfile')
    parser.add_argument('--verbose', type=bool, default=False)
    parser.add_argument('--store', type=bool, default=False)

    args = parser.parse_args()

    dw8000_reverse_engineer.remap_tape_data_to_syx(tapefile=args.binfile, syxfile=args.syxfile, verbose=args.verbose, store=args.store)


if __name__ == '__main__':
    bin2syx()
