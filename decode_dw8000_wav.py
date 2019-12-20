import wave
import struct
import numpy
import os
import scipy.io.wavfile as wf
from scipy.signal import butter, lfilter
from reverseEngineerDW8000 import read_acoustic_bytes

verbose = True

middle_length = 21
too_long = 100


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
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


def load_wav(wave_file_name):
    print("Reading file", wave_file_name)

    try:
        fs, all_channels = wf.read(wave_file_name)

        # If this is a multi-channel (Stereo) file, use only the first channel
        if (len(all_channels.shape)) > 1:
            data = all_channels[:, 0]
        else:
            data = all_channels
        return fs, data
    except ValueError:
        # Not all files can be read by scipy, if the file is old and corrupt, try the standard wave lib
        with wave.open(wave_file_name) as wavefile:
            fs = wavefile.getparams().framerate
            all_bytes = wavefile.readframes(wavefile.getnframes())
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


def transform_wav_to_bytes(wave_file_name, output_file_name):

    fs, data = load_wav(wave_file_name)

    if verbose:
        print("Sample rate %dHz" % fs)

    # If this is slower than 44kHz, double entries
    if fs < 44000:
        if verbose:
            print("Sample frequency is less than 44000, upsampling...")
        while fs < 44000:
            newdata = data.repeat(2)
            data = newdata
            fs *= 2


    max_value = max(abs(numpy.min(data)), abs(numpy.max(data)))
    average = numpy.average(data) # Gleichstromanteil
    if verbose:
        print("Min: ", numpy.min(data), ", and max ", numpy.max(data), "average is ", numpy.average(data))
    normaldata = (data - average) / max_value

    # The settings for hysteresis in the Schmitt-Trigger
    high = 0.05
    low = -0.05
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
        #max_value = max(abs(numpy.min(filtered)), abs(numpy.max(filtered)))
        #filtered = filtered / max_value
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
        if not signal in histogram:
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

    print("Writing file", output_file_name)
    with open(output_file_name, "wb") as newFile:
        newFile.write(bytearray(bytestream))

    # Check for checksum errors by reading the bytes
    if verbose:
        print("Reading result to check for checksum errors!")
    if read_acoustic_bytes(output_file_name):
        print("Successfully verified file", output_file_name)
    else:
        print("File could not be read:", output_file_name)
        print_histogram(histogram)


transform_wav_to_bytes(r"g:\christof\music\dw8000\patches\Clipped.wav", "tmp.bin")
exit()

for root, dirs, files in os.walk(r"g:\christof\music\dw8000\patches"):
    for file in files:
        filename, file_extension = os.path.splitext(file)
        if file_extension.lower() == ".wav":
            transform_wav_to_bytes(os.path.join(root, file), os.path.join(root, filename + ".auto.bin"))
