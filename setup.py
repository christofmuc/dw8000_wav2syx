import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dw8000_wav2syx-christofmuc", # Replace with your own username
    version="1.0.0",
    author="Christof",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/christofmuc/dw8000_wav2syx",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: AGPL-3.0 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'dw8000_bin2syx= dw8000_wav2syx.dw8000_bin2syx',
            'dw8000_wav2bin= dw8000_wav2syx.dw8000_wav2bin',
            'dw8000_wav2syx= dw8000_wav2syx.dw8000_wav2syx',
        ]
    }
)
