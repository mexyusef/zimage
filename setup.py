#!/usr/bin/env python3
"""
Setup script for ZImage
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="zimage",
    version="1.0.0",
    author="Yusef Ulum",
    author_email="yusef314159@gmail.com",
    description="A professional-grade image management and editing solution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mexyusef/zimage",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Editors",
    ],
    python_requires=">=3.7",
    install_requires=[
        "PyQt6>=6.2.0",
        "Pillow>=9.0.0",
        "numpy>=1.21.0",
        "exifread>=2.3.2",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-qt>=4.0.0",
            "pylint>=2.10.0",
            "black>=21.7b0",
        ],
        "windows": ["pywin32>=304"],
    },
    entry_points={
        "console_scripts": [
            "zimage=zimage.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "zimage": [
            "resources/icons/*.png",
            "resources/styles/*.qss",
            "resources/themes/*.json",
            "resources/translations/*.qm",
        ],
    },
)
