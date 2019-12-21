# Introduction

This is a little command line tool that allows you to convert files stored in the [Korg DW-8000](https://en.wikipedia.org/wiki/Korg_DW-8000) specific WAV format into much easier to handle MIDI Sysex SYX files. 

The Korg DW8000 synthesizer is from an area, when tape storage for computer data was still the cheapest and therefore most widespread option. Think Commodore C64 or Sinclair Spectrum, which stored programs and data on common audio tapes, in Sinclair's case even on standard audio hardware like a casette recorder that will already have been in the household back in 1982. 

As the tape is really just a storage for audio data, nowadays this data is usually kept in WAV format, which is the digitized version of the data. But the Korg DW8000 also supports a full MIDI implmentation, and actually it is much nicer to work with MIDI and its digital serial data than with WAV files.

It took a little reverse engineering exercise, because the tape format of the Korg DW8000 is not the same as the sysex format, but rather - I guess - a simple memory dump of the device. And as RAM was precious, the engineers have squeezed the 51 bytes of sysex data into 31 bytes on tape and probably RAM. They even split up a single data item over 2 storage addresses, which makes the reverse engineering a bit harder than it looked at start.

# Download and Usage

This tool is implemented in [Python](https://python.org), so you will need a working python installation (version 3.6 and newer). If you have that, installation of the tool is as easy as installing it from [pypi](https://pypi.org/project/dw8000-wav2syx-christofmuc/)

    pip install dw8000_wav2syx-christofmuc

This will install three command line tools, of which you will probably wnat to use only one. To convert a WAV file into a SYX file that you can e.g. send to your Korg with Midi-OX, just type

    dw8000_wav2syx --store True "Volume 8.wav" Volume8.syx

to create the Volume8.syx file. The `--store True` part instructs the converter to create sysex write requests between the patches, which turns the sysex file into a proper bank dump. Without these, the file is a list of edit buffer dumps, and if you send the file to the synth, only the last patch sent will be in the edit buffer, all others will have been lost.

***WARNING***: Sending the file created with --store True to your DW8000 will overwrite all patches, make sure to backup first!

## In case of problems

Not all files I found in the Internet could be converted, some have a really bad quality and might have also errors in the audio (some of these old tape drives were really no nicely adjusted) that make my simple problem fail. 

I am interested in trying to load more complicated error cases, so feel free to contact me and provide me with the WAV files that don't load, maybe there is a chance to scratch the data from the WAV file anyway.

## Other uses

If you want to see what is actually stored on tape, you can run the same conversion process in two steps:

    dw8000_wav2bin "Volume 8.wav" Volume8.bin

will create a binary file that contains all the bytes as they are written on the tape. Use a hex editor to see what's in there. The second step just does

    dw8000_bin2sys Volume8.bin Volume8.syx

converting the bin file to the sysex representation, effectively completing the transform.

## How it works

There were many ways to store data on tape back in the 80s, luckily the DW8000 service manual even provided a lot of information on the format. 

Scratching the bits from the WAV file is really just measuring the length of the zero crossings of the signal, and classifying the length as either a long (0) or a short (1) rectangle. It won't look very rectangular if you look at the WAV file e.g. with Audacity, but that can be contributed to the low-pass filtering expected on an old audio tape, and should not endanger the conversion.

Once you have the bits, detecting the bytes is simple given they are stored with two start and one stop bit, converting the bitstream into a bytestream.

The much harder problem was the reverse engineering of the memory layout, as the tape data is just a memory dump. I even disassembled the DW8000 firmware while trying to figure it out, but in the end generating test data was easier, treating the device as a black box which's behavior can be observed from the outside.


## Licensing

As some substantial work has gone into the development of this, I decided to offer a dual license - AGPL, see the LICENSE file for the details, for everybody interested in how this works and willing to spend some time her- or himself on this, and a commercial MIT license available from me on request. Thus I can help the OpenSource community without blocking possible commercial applications.

## Contributing

All pull requests and issues welcome, I will try to get back to you as soon as I can. Due to the dual licensing please be aware that I will need to request transfer of copyright on accepting a PR. 

## About the author

Christof is a lifelong software developer having worked in various industries, and can't stop his programming hobby anyway. 
