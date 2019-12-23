#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

import argparse
import tempfile

from dw8000_wav2syx import dw8000_wav2bin
from dw8000_wav2syx import dw8000_reverse_engineer


def wav2syx():
    parser = argparse.ArgumentParser(prog="dw8000_wav2syx", description='Convert a Korg DW8000 tape wav into syx format')
    parser.add_argument('wavfile')
    parser.add_argument('syxfile')
    parser.add_argument('--verbose', type=bool, default=False)
    parser.add_argument('--store', type=bool, default=False)

    args = parser.parse_args()

    with tempfile.TemporaryFile() as bin_file:
        worked = dw8000_wav2bin.transform_wav_to_bytes(args.wavfile, bin_file, verbose=args.verbose)
        if worked:
            # Rewind bin file so the next function will read from the start again
            bin_file.seek(0)
            dw8000_reverse_engineer.remap_tape_data_to_syx(tapefile=bin_file, syxfile= args.syxfile, verbose=args.verbose, store=args.store)


if __name__ == '__main__':
    wav2syx()
