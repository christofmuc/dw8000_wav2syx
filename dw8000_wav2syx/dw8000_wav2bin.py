#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

import argparse
import wave
import struct
import numpy
import scipy.io.wavfile as wf
from scipy.signal import butter, lfilter
from dw8000_wav2syx import dw8000_reverse_engineer

middle_length = 21
too_long = 100


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    # noinspection PyTupleAssignmentBalance
    b, a = butter(order, normal_cutoff, btype='low', analog=False, output='ba')
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


def amplitude_histogram(data):
    return numpy.histogram(data, 20)


def data_is_clipped(data):
    histo, bins = amplitude_histogram(data)
    if histo[0] > histo[1] and histo[19] > histo[18]:
        print("Signal appears to be clipped")
        return True
    return False


def load_wav(wave_file_name, verbose = False):
    print("Reading file", wave_file_name)

    try:
        fs, all_channels = wf.read(wave_file_name)
        print("Successfully read file using scipy.io.wavfile, samplerate is %d" % (fs))
        # If this is a multi-channel (Stereo) file, use only the first channel
        if (len(all_channels.shape)) > 1:
            data = all_channels[:, 0]
            if verbose:
                print("File is stereo, using only left (first) channel")
        else:
            data = all_channels
        return fs, data
    except ValueError:
        print("Failed to read wavfile with scipy.io.wavfile, fallback to old wave library")
        # Not all files can be read by scipy, if the file is old and corrupt, try the standard wave lib
        with wave.open(wave_file_name) as wavefile:
            fs = wavefile.getparams().framerate
            all_bytes = wavefile.readframes(wavefile.getnframes())
            if verbose:
                print("Read %d samples at %d Hz sample rate and %d bytes per sample" %
                      (wavefile.getnframes(), fs, wavefile.getparams().sampwidth))
            formatstring = ""
            if wavefile.getparams().sampwidth == 2:
                formatstring = '%dh' % (len(all_bytes) / struct.calcsize('h'))
            elif wavefile.getparams().sampwidth == 1:
                formatstring = '%db' % (len(all_bytes) / struct.calcsize('b'))
            else:
                print("Unsupported sample width in wave file of", wavefile.getparams().sampwidth)
                exit(-1)
            data = numpy.array(struct.unpack(formatstring, all_bytes))
            return fs, data


def print_histogram(histogram):
    for key in sorted(histogram.keys()):
        print("%d : %d" % (key, histogram[key]))


def schmitt_trigger(normaldata, high, low):
    readptr = 0
    signal = -1
    rect = numpy.array(normaldata)
    while readptr < len(normaldata):
        if signal == -1:
            if normaldata[readptr] > high:
                # Up flank
                signal = 1
        else:
            if normaldata[readptr] < low:
                # Down flank
                signal = -1
        rect[readptr] = signal
        readptr += 1
    return rect


def transform_wav_to_bytes(wave_file_name, output_file, hysteresis_threshold=0.05, lowpass=True, verbose=False):
    fs, data = load_wav(wave_file_name, verbose)

    # If this is slower than 44kHz, double entries
    if fs < 44000:
        if verbose:
            print("Sample frequency is less than 44000, upsampling...")
        while fs < 44000:
            newdata = data.repeat(2)
            data = newdata
            fs *= 2

    max_value = max(abs(numpy.min(data)), abs(numpy.max(data)))
    average = numpy.average(data)  # Gleichstromanteil
    if verbose:
        print("Min: ", numpy.min(data), ", and max ", numpy.max(data), "average is ", numpy.average(data))
    normaldata = (data - average) / max_value

    # The settings for hysteresis in the Schmitt-Trigger
    high = hysteresis_threshold
    low = -hysteresis_threshold
    if data_is_clipped(normaldata):
        # Clipped data can be processed differently than non-clipped data, as it does not make sense to low pass
        # We treat this as a nearly rectangular signal
        high = 0.8
        low = -0.8
    else:
        # Filter requirements.
        order = 5
        cutoff = 3125  # desired cutoff frequency of the filter, Hz
        filtered = butter_lowpass_filter(data=normaldata, cutoff=cutoff, fs=fs, order=order)
        if verbose:
            print("Filtered Min: ", numpy.min(filtered), ", and max ", numpy.max(filtered))
        # max_value = max(abs(numpy.min(filtered)), abs(numpy.max(filtered)))
        # filtered = filtered / max_value
        if lowpass:
            # Use the lowpass filtered data instead of the simple normalized data
            normaldata = filtered

    if verbose:
        print(normaldata[172000:204000])

    # Schmitt-trigger this to create a rectangle
    rect = schmitt_trigger(normaldata, high, low)

    if verbose:
        print(rect[172000:194000])

    # Now, build histogram of lengths
    readptr = 0
    oldptr = 0
    signal = rect[0]
    signal_lengths = []
    while readptr < len(rect):
        if rect[readptr] != signal:
            # Flank, record position and store length. Don't record 0 length
            if readptr > oldptr:
                signal_lengths.append(readptr - oldptr)
            signal = rect[readptr]
            oldptr = readptr
        readptr += 1

    signals = numpy.array(signal_lengths)
    if verbose:
        print(signals, "Length", len(signals))
    histogram = {}
    for signal in signals:
        if signal not in histogram:
            histogram[signal] = 0
        histogram[signal] += 1

    if verbose:
        print_histogram(histogram)

    # Now convert into a bit stream
    bitstream = []
    for signal in signals:
        if signal > too_long:
            if verbose:
                print("Ignoring signal of length %d" % signal)
        if signal < middle_length:
            bitstream.append(1)
        else:
            bitstream.append(0)

    # print(bitstream)
    if verbose:
        print("Number of bits and bytes:", len(bitstream), len(bitstream) / 8.0)

    # Now make the byte stream
    bytestream = []
    readptr = 0
    had_good_byte = False
    while readptr < (len(bitstream) - 10):
        # 1 start bit high and two stop bits low?
        if bitstream[readptr] == 0 and bitstream[readptr + 10] == 1 and bitstream[readptr + 9] == 1:
            # Good byte
            byte_extracted = bitstream[readptr + 1: readptr + 9]
            # Build byte - assume low bit first
            byte_as_value = 0
            for bit in byte_extracted:
                byte_as_value >>= 1
                if bit == 1:
                    byte_as_value |= 128

            bytestream.append(byte_as_value)
            readptr += 11
            had_good_byte = True
        else:
            # Try starting at the next bit
            if had_good_byte:
                if verbose:
                    print("Bad byte at byte %04x " % (readptr >> 3), bitstream[readptr: readptr + 11])
            had_good_byte = False
            readptr += 1

    # print(bytestream)
    if verbose:
        print(len(bytestream))

    # Write to file given
    output_file.write(bytearray(bytestream))

    # Check for checksum errors by reading the bytes
    if verbose:
        print("Reading result to check for checksum errors!")

    # Rewind and reread file
    output_file.seek(0)
    if dw8000_reverse_engineer.read_acoustic_bytes(output_file):
        print("Successfully verified file")
        return True
    else:
        print("File could not be verified!")
        print_histogram(histogram)
        return False


def wav2bin():
    parser = argparse.ArgumentParser(description='Convert a Korg DW8000 wave file to its binary representation in '
                                                 '.bin format')
    parser.add_argument('wavefile')
    parser.add_argument('binfile')
    parser.add_argument('--lowpass', type=bool, default=True)
    parser.add_argument('--threshold', type=float, default=0.05)
    parser.add_argument('--verbose', type=bool, default=False)

    args = parser.parse_args()

    with open(args.binfile, "w+b") as bin_file:
        transform_wav_to_bytes(args.wavefile, bin_file, hysteresis_threshold=args.threshold,
                                                        lowpass=args.lowpass, verbose=args.verbose)


# If this is the main program, we only do a WAV to binary conversion, we do not create a syx file but rather stop
# at the phase where we get the binary data, so we can see what is on the tape
if __name__ == "__main__":
    wav2bin()
