#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

import os

from dw8000_wav2syx.dw8000_wav2bin import transform_wav_to_bytes

for root, dirs, files in os.walk(r"g:\christof\music\dw8000\patches"):
    for file in files:
        filename, file_extension = os.path.splitext(file)
        if file_extension.lower() == ".wav":
            transform_wav_to_bytes(os.path.join(root, file), os.path.join(root, filename + ".auto.bin"))
