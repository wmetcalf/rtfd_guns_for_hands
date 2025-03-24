# setup.py
from setuptools import setup, find_packages

setup(
    name="rtfd_guns_for_hands",
    version="0.2.0",
    description="Parser for RTFD 'guns for hands' combined marker blocks with padded file data",
    author="Node5,adepasquale",
    packages=find_packages(),
    install_requires=[
        "python-magic",
    ],
    entry_points={
        "console_scripts": [
            "rtfd-guns-parse = rtfd_guns_for_hands.cli:main"
        ]
    },
    python_requires=">=3.8",
)
