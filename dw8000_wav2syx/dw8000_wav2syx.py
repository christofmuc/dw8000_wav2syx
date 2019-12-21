#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

import argparse
import tempfile

from dw8000_wav2syx.dw8000_wav2bin import transform_wav_to_bytes
from dw8000_wav2syx.dw8000_reverse_engineer import remap_tape_data_to_syx


def wav2syx():
    parser = argparse.ArgumentParser(description='Convert a Korg DW8000 tape wav into syx format')
    parser.add_argument('wavfile')
    parser.add_argument('syxfile')
    parser.add_argument('--verbose', type=bool, default=False)
    parser.add_argument('--store', type=bool, default=False)

    args = parser.parse_args()

    with tempfile.TemporaryFile() as bin_file:
        transform_wav_to_bytes(args.wavfile, bin_file, verbose=args.verbose)
        # Rewind bin file so the next function will read from the start again
        bin_file.seek(0)
        remap_tape_data_to_syx(tapefile=bin_file, syxfile= args.syxfile, verbose=args.verbose, store=args.store)


if __name__ == '__main__':
    wav2syx()
