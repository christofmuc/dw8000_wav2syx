#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

import os

from dw8000_wav2syx.dw8000_wav2bin import transform_wav_to_bytes
from dw8000_wav2syx.dw8000_reverse_engineer import remap_tape_data_to_syx

for root, dirs, files in os.walk(r"test_data"):
    for file in files:
        filename, file_extension = os.path.splitext(file)
        if file_extension.lower() == ".wav":
            output_filename = os.path.join(root, filename + ".auto.bin")
            with open(output_filename, "w+b") as output_file:
                worked = transform_wav_to_bytes(os.path.join(root, file), output_file)
                if worked:
                    # Rewind bin file so the next function will read from the start again
                    output_file.seek(0)
                    syx_filename = os.path.join(root, filename + ".auto.syx")
                    remap_tape_data_to_syx(tapefile=output_file, syxfile=syx_filename)

