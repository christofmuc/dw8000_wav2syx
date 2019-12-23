#
#  Copyright (c) 2019 Christof Ruch. All rights reserved.
#
#  Dual licensed: Distributed under Affero GPL license by default, an MIT license is available for purchase
#

from math import log2, floor
import argparse
import mido

recalculate = False


def is_single_buffer_dump(syx):
    # Korg DW8000 edit buffer
    return syx.data[0] == 0x42 and (syx.data[1] & 0xf0) == 0x30 and syx.data[2] == 0x03 and syx.data[3] == 0x40


def read_sysex(filename):
    original_data = []
    messages = mido.read_syx_file(filename)
    for message in messages:
        if is_single_buffer_dump(message):
            original_data.append(message.data[4:])
    return original_data


def print_input_data(bin_array):
    for i in range(len(bin_array)):
        print("%i:%s " % (i, '{:02x}'.format(bin_array[i])), end='')
    print()


def binstring_2(value):
    return format(value, '#010b')


def binstring(num, length=8):
    return format(num, '#0{}b'.format(length + 2))


# In a single bin file, we might have more than one instance of the patch data. This normally happens as
# users will want to write the same data multiple times in order to have a backup, given how unsafe tape storage was
# This function only loads the first instance (?)
def read_acoustic_bytes(bytefile):
    acoustic_data = []
    header_found = False
    intro_done = False
    count = 0
    success = True
    while bytefile.readable() and count < 64:
        if not header_found:
            data = bytefile.read(1)
            if data[0] == 0xff:
                header_found = True
        elif not intro_done:
            data = bytefile.read(1)
            if data[0] != 0xff:
                # This is the first byte of the intro
                if data[0] != 0x42:
                    # print("Incorrect header - corrupt file?")
                    header_found = False
                    continue
                second = bytefile.read(1)
                if second[0] != 0x03:
                    print("Are you sure this is a file for the Korg DW8000? Found Device ID", second[0])
                    header_found = False
                    continue
                intro_done = True
        else:
            patch = bytefile.read(30)
            checksum = bytefile.read(1)
            if len(checksum) == 0:
                print("Premature end of file!")
                success = False
            elif (sum(patch) & 0xff) != checksum[0]:
                print("Checksum error got %x but expected %x" % (sum(patch) & 0xff, checksum[0]))
                success = False
            acoustic_data.append(patch)
            # print("Patch %d" % count, patch)
            count += 1
    return count == 64 and success, acoustic_data


# Hand code the one special case for parameter #32, which is split into two bytes on tape
# The rest can be detected automatically
# secret_mapping = [{"shift": 0, "sysex": 32, "audio": 18, "bits": 3},
#                  {"shift": 6, "sysex": 32, "audio": 19, "bits": 2, "leftshift": 3}]


def find_secret_mapping(original_data, acoustic_data):
    # Now search the 51 parameters!
    for param in range(51):
        original = original_data[param]
        param_no = param
        for original_position in range(51):
            if original[original_position] != 0:
                break

        if param_no == -1:
            print("No value found for param no", param)
            continue

        value_to_find = original[param_no]
        if value_to_find == 0:
            print("No value for param %d in " % param_no, original)
            continue
        acoustic = acoustic_data[param]
        found = False
        for position in range(30):
            for shift in range(8):
                if (acoustic[position] >> shift) == value_to_find:
                    print("Found parameter #%d at position %d with shift %d" % (param, position, shift))
                    bits = floor(log2(value_to_find) + 1)
                    secret_mapping.append({"sysex": param_no, "audio": position, "shift": shift, "bits": bits})
                    found = True

        if not found:
            print("Could not find param #%d with value %d " % (param, value_to_find))
            print("Sysex: ", original)
            print("Tape: ", acoustic)


if recalculate:
    sysex_data = read_sysex(r"dw8000-reverse\reveng.syx")
    with open(r"dw8000-reverse\reverse.bin", "rb") as reverse_file:
        read_correctly, tape_data = read_acoustic_bytes(reverse_file)
        if not read_correctly:
            print("Fatal - could not decode reverse engineering tape file")
            exit(-1)
        find_secret_mapping(original_data=sysex_data, acoustic_data=tape_data)
else:
    # Override the secret mapping with the result of the automatic mapping
    secret_mapping = [{"leftshift": 2, "audio": 18, "bits": 3, "sysex": 32, "shift": 0},
                      {"audio": 19, "bits": 2, "sysex": 32, "shift": 6},
                      {"audio": 1, "bits": 2, "sysex": 0, "shift": 5},
                      {"audio": 0, "bits": 4, "sysex": 1, "shift": 0},
                      {"audio": 1, "bits": 5, "sysex": 2, "shift": 0},
                      {"audio": 3, "bits": 2, "sysex": 3, "shift": 5},
                      {"audio": 3, "bits": 1, "sysex": 4, "shift": 7},
                      {"audio": 19, "bits": 5, "sysex": 5, "shift": 0},
                      {"audio": 3, "bits": 5, "sysex": 6, "shift": 0},
                      {"audio": 2, "bits": 2, "sysex": 7, "shift": 5},
                      {"audio": 0, "bits": 4, "sysex": 8, "shift": 4},
                      {"audio": 2, "bits": 5, "sysex": 9, "shift": 0},
                      {"audio": 4, "bits": 3, "sysex": 10, "shift": 0},
                      {"audio": 6, "bits": 3, "sysex": 11, "shift": 0},
                      {"audio": 4, "bits": 5, "sysex": 12, "shift": 3},
                      {"audio": 26, "bits": 2, "sysex": 13, "shift": 0},
                      {"audio": 29, "bits": 6, "sysex": 14, "shift": 0},
                      {"audio": 5, "bits": 6, "sysex": 15, "shift": 2},
                      {"audio": 6, "bits": 5, "sysex": 16, "shift": 3},
                      {"audio": 5, "bits": 2, "sysex": 17, "shift": 0},
                      {"audio": 1, "bits": 1, "sysex": 18, "shift": 7},
                      {"audio": 7, "bits": 5, "sysex": 19, "shift": 3},
                      {"audio": 8, "bits": 5, "sysex": 20, "shift": 0},
                      {"audio": 9, "bits": 5, "sysex": 21, "shift": 0},
                      {"audio": 10, "bits": 5, "sysex": 22, "shift": 0},
                      {"audio": 11, "bits": 5, "sysex": 23, "shift": 0},
                      {"audio": 12, "bits": 5, "sysex": 24, "shift": 0},
                      {"audio": 13, "bits": 5, "sysex": 25, "shift": 0},
                      {"audio": 7, "bits": 3, "sysex": 26, "shift": 0},
                      {"audio": 14, "bits": 5, "sysex": 27, "shift": 0},
                      {"audio": 15, "bits": 5, "sysex": 28, "shift": 0},
                      {"audio": 16, "bits": 5, "sysex": 29, "shift": 0},
                      {"audio": 17, "bits": 5, "sysex": 30, "shift": 0},
                      {"audio": 18, "bits": 5, "sysex": 31, "shift": 3},
                      {"audio": 20, "bits": 3, "sysex": 33, "shift": 0},
                      {"audio": 27, "bits": 2, "sysex": 34, "shift": 0},
                      {"audio": 20, "bits": 5, "sysex": 35, "shift": 3},
                      {"audio": 23, "bits": 5, "sysex": 36, "shift": 3},
                      {"audio": 24, "bits": 5, "sysex": 37, "shift": 3},
                      {"audio": 25, "bits": 5, "sysex": 38, "shift": 3},
                      {"audio": 22, "bits": 4, "sysex": 39, "shift": 0},
                      {"audio": 2, "bits": 1, "sysex": 40, "shift": 7},
                      {"audio": 21, "bits": 3, "sysex": 41, "shift": 0},
                      {"audio": 22, "bits": 4, "sysex": 42, "shift": 4},
                      {"audio": 28, "bits": 4, "sysex": 43, "shift": 4},
                      {"audio": 27, "bits": 5, "sysex": 44, "shift": 3},
                      {"audio": 21, "bits": 5, "sysex": 45, "shift": 3},
                      {"audio": 28, "bits": 4, "sysex": 46, "shift": 0},
                      {"audio": 26, "bits": 5, "sysex": 47, "shift": 3},
                      {"audio": 23, "bits": 2, "sysex": 48, "shift": 0},
                      {"audio": 24, "bits": 2, "sysex": 49, "shift": 0},
                      {"audio": 25, "bits": 2, "sysex": 50, "shift": 0}]


# print("Mapping used", json.dumps(secret_mapping))


def mask_for_bits(bits):
    return (1 << bits) - 1


def remap_tape_data_to_syx(tapefile, syxfile, ground_truth=None, verbose=False, store=False):
    original_data = []
    if ground_truth is not None:
        original_data = read_sysex(ground_truth)
        if verbose:
            print("Original syswx: ", original_data)

    worked, acoustic_data = read_acoustic_bytes(tapefile)
    if not worked:
        print("Fatal error - could not verify acoustic data, tape transcoding didn't work")
        return
    if verbose:
        print("Found %d messages in file, expected 64" % len(acoustic_data))
        print("Original tape: ", acoustic_data)

    # Now use the mapping...
    new_sysex = []
    index = 0
    for tune_data in acoustic_data:
        # Create empty sysex patch, 51 bytes
        new_data = [0 for _ in range(51)]
        for key in secret_mapping:
            if "leftshift" in key:
                new_data[key["sysex"]] = new_data[key["sysex"]] | (
                        ((tune_data[key["audio"]] & (mask_for_bits(key["bits"]) << key["shift"])) >> key["shift"]) <<
                        key[
                            "leftshift"])
            else:
                new_data[key["sysex"]] = new_data[key["sysex"]] | (
                        (tune_data[key["audio"]] & (mask_for_bits(key["bits"]) << key["shift"])) >> key["shift"])

        # Validation step - if we know the expected outcome, check if our secret mapping worked!
        if ground_truth is not None:
            if not (new_data == list(original_data[index])):
                # print("Match error at index %d" % index)
                # print_input_data(acoustic_data[index])
                # print("Truth", list(original_data[index]))
                # print("Found", new_data)
                print("Mapping input 18 %s 19 %s wanted %s but got %s" % (binstring(tune_data[18]),
                                                                          binstring(tune_data[19]),
                                                                          binstring(original_data[index][32]),
                                                                          binstring(new_data[32])))

        # Create a DW8000 Data Save sysex message according to its service manual (p. 3)
        data_dump = [0x42, 0x30, 0x03, 0x40]
        data_dump.extend(new_data)
        data_dump_message = mido.Message('sysex', data=data_dump)
        new_sysex.append(data_dump_message)

        if store:
            # If the store parameter is selected, create a write request that will store the edit buffer just
            # created into a patch memory place
            if 0 <= index < 64:
                write_request = mido.Message('sysex', data=[0x42, 0x30, 0x03, 0x11, index])
                new_sysex.append(write_request)
            else:
                print("Error: More than 64 patches, can't create write request any more")
        index += 1

    if verbose:
        print("Output after mapping", new_sysex)
    mido.write_syx_file(syxfile, new_sysex)
    print(syxfile, "written")


def bin2syx_reverse():
    parser = argparse.ArgumentParser(description='Calculate the mapping and verify the result')
    parser.add_argument('binfile')
    parser.add_argument('known_syxfile')
    parser.add_argument('syxfile')
    parser.add_argument('--verbose', type=bool, default=False)

    args = parser.parse_args()
    # This is the data to reverse engineer the memory mapping
    with open(args.binfile, "rb") as bin_file:
        remap_tape_data_to_syx(tapefile=bin_file, ground_truth=args.known_syxfile, syxfile=args.syxfile,
                               verbose=args.verbose)


if __name__ == '__main__':
    bin2syx_reverse()
