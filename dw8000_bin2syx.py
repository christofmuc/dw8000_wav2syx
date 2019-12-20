#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

import argparse
from reverseEngineerDW8000 import remap_tape_data_to_syx

verbose = False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert a Korg DW8000 bin file converted from tape into syx format')
    parser.add_argument('binfile')
    parser.add_argument('syxfile')
    parser.add_argument('--verbose', type=bool, default=False)

    args = parser.parse_args()

    verbose = args.verbose
    remap_tape_data_to_syx(tapefile=args.binfile, syxfile= args.syxfile)

