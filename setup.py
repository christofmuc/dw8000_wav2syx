import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dw8000_wav2syx-christofmuc",  # Replace with your own username
    version="1.0.5",
    author="Christof",
    author_email="christof.ruch@gmail.com",
    description="Convert data for the Korg DW8000 stored as tape wav files into MIDI sysex format.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/christofmuc/dw8000_wav2syx",
    download_url="",  # This should point to github releases?
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "mido",
        "scipy"
    ],
    entry_points={
        'console_scripts': [
            'dw8000_bin2syx= dw8000_wav2syx.dw8000_bin2syx:bin2syx',
            'dw8000_wav2bin= dw8000_wav2syx.dw8000_wav2bin:wav2bin',
            'dw8000_wav2syx= dw8000_wav2syx.dw8000_wav2syx:wav2syx',
        ]
    }
)
